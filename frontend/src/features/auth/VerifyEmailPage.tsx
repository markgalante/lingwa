import {useState, useEffect} from 'react';
import {useNavigate, useSearchParams} from 'react-router-dom';
import {api} from '../../api/client';
import {useAuth} from '../../context/auth/useAuth';
import {useAppForm} from '../../hooks/useAppForm';
import {FormField} from '../../components/ui/FormField';
import {passwordStepSchema, nameStepSchema, resendSchema} from '../../schemas/auth';

interface TokenResponse {
  access_token: string;
}

type Step = 'password' | 'name';

export function VerifyEmailPage() {
  const [searchParams] = useSearchParams();
  const {login} = useAuth();
  const navigate = useNavigate();

  const token = searchParams.get('token');

  const [step, setStep] = useState<Step>('password');
  const [password, setPassword] = useState('');
  const [serverError, setServerError] = useState<string | null>(null);
  const [linkExpired, setLinkExpired] = useState(!token);
  const [checking, setChecking] = useState(!!token);

  useEffect(() => {
    if (!token) return;
    api
      .get(`/auth/check-verification-token?token=${token}`)
      .catch(() => setLinkExpired(true))
      .finally(() => setChecking(false));
    // intentionally runs once — searchParams is not a stable reference
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const passwordForm = useAppForm({
    defaultValues: {password: '', confirmPassword: ''},
    validators: {onSubmit: passwordStepSchema},
    onSubmit: ({value}) => {
      setPassword(value.password);
      setStep('name');
    },
  });

  const nameForm = useAppForm({
    defaultValues: {name: ''},
    validators: {onSubmit: nameStepSchema},
    onSubmit: async ({value}) => {
      setServerError(null);
      try {
        const {access_token} = await api.post<TokenResponse>('/auth/complete-registration', {
          token,
          name: value.name.trim(),
          password,
          confirm_password: password,
        });
        await login(access_token);
        navigate('/dashboard', {replace: true});
      } catch (err) {
        if (err instanceof Error && err.message.includes('400')) {
          setLinkExpired(true);
        } else {
          setServerError('Something went wrong. Please try again.');
        }
      }
    },
  });

  if (checking) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950">
        <p className="text-gray-400 text-sm">Verifying your link…</p>
      </div>
    );
  }

  if (linkExpired) {
    return <ResendForm />;
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950">
      <div className="w-full max-w-sm p-8 rounded-2xl bg-gray-900 shadow-xl flex flex-col gap-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-white tracking-tight">Lingwa</h1>
          <p className="mt-2 text-gray-400 text-sm">
            {step === 'password' ? "Let's set up your account" : 'What should we call you?'}
          </p>
        </div>

        {step === 'password' ? (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              e.stopPropagation();
              passwordForm.handleSubmit();
            }}
            className="flex flex-col gap-4"
          >
            <passwordForm.Field name="password">
              {(field) => (
                <FormField
                  field={field}
                  label="Password"
                  type="password"
                  placeholder="Min. 8 characters"
                  autoComplete="new-password"
                  autoFocus
                />
              )}
            </passwordForm.Field>

            <passwordForm.Field name="confirmPassword">
              {(field) => (
                <FormField
                  field={field}
                  label="Confirm password"
                  type="password"
                  placeholder="Repeat your password"
                  autoComplete="new-password"
                />
              )}
            </passwordForm.Field>

            {serverError && <p className="text-red-400 text-sm">{serverError}</p>}

            <button
              type="submit"
              className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-colors"
            >
              Continue
            </button>
          </form>
        ) : (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              e.stopPropagation();
              nameForm.handleSubmit();
            }}
            className="flex flex-col gap-4"
          >
            <nameForm.Field name="name">
              {(field) => (
                <FormField
                  field={field}
                  label="Full name"
                  type="text"
                  placeholder="Your name"
                  autoComplete="name"
                  autoFocus
                />
              )}
            </nameForm.Field>

            {serverError && <p className="text-red-400 text-sm">{serverError}</p>}

            <div className="flex flex-col gap-2">
              <nameForm.Subscribe selector={(state) => state.isSubmitting}>
                {(isSubmitting) => (
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-sm transition-colors"
                  >
                    {isSubmitting ? 'Creating account…' : 'Create account'}
                  </button>
                )}
              </nameForm.Subscribe>
              <button
                type="button"
                onClick={() => {
                  setStep('password');
                  setServerError(null);
                }}
                className="text-gray-500 hover:text-gray-400 text-sm"
              >
                Back
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

export default VerifyEmailPage;

function ResendForm() {
  const [sent, setSent] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const form = useAppForm({
    defaultValues: {email: ''},
    validators: {onSubmit: resendSchema},
    onSubmit: async ({value}) => {
      setServerError(null);
      try {
        await api.post('/auth/resend-verification', {email: value.email});
        setSent(true);
      } catch (err) {
        if (err instanceof Error && err.message.includes('404')) {
          setServerError(
            'No pending account found for that email. Check for a typo or sign up again.'
          );
        } else {
          setServerError('Something went wrong. Please try again.');
        }
      }
    },
  });

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950">
      <div className="w-full max-w-sm p-8 rounded-2xl bg-gray-900 shadow-xl flex flex-col gap-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-white tracking-tight">Lingwa</h1>
          <p className="mt-2 text-gray-400 text-sm">
            {sent ? 'Check your email' : 'Your link has expired'}
          </p>
        </div>

        {sent ? (
          <p className="text-gray-400 text-sm text-center">
            We sent a new verification link to{' '}
            <span className="text-white">{form.state.values.email}</span>.
          </p>
        ) : (
          <form
            onSubmit={(e) => {
              e.preventDefault();
              e.stopPropagation();
              form.handleSubmit();
            }}
            className="flex flex-col gap-4"
          >
            <p className="text-gray-400 text-sm">
              Enter your email and we'll send you a fresh link.
            </p>

            <form.Field name="email">
              {(field) => (
                <FormField
                  field={field}
                  label="Confirm your email"
                  type="email"
                  placeholder="you@example.com"
                  autoComplete="email"
                  autoFocus
                />
              )}
            </form.Field>

            {serverError && <p className="text-red-400 text-sm">{serverError}</p>}

            <form.Subscribe selector={(state) => state.isSubmitting}>
              {(isSubmitting) => (
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-sm transition-colors"
                >
                  {isSubmitting ? 'Sending…' : 'Resend verification email'}
                </button>
              )}
            </form.Subscribe>
          </form>
        )}
      </div>
    </div>
  );
}
