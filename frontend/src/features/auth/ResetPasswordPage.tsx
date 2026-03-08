import {useState, useEffect} from 'react';
import {Link, useNavigate, useSearchParams} from 'react-router-dom';
import {api} from '../../api/client';
import {useAppForm} from '../../hooks/useAppForm';
import {FormField} from '../../components/ui/FormField';
import {resetPasswordSchema} from '../../schemas/auth';

export function ResetPasswordPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const token = searchParams.get('token');

  const [tokenValid, setTokenValid] = useState<boolean | null>(null);
  const [success, setSuccess] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setTokenValid(false);
      return;
    }
    api
      .get(`/auth/check-reset-token?token=${token}`)
      .then(() => setTokenValid(true))
      .catch(() => setTokenValid(false));
    // intentionally runs once — searchParams is not a stable reference
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const form = useAppForm({
    defaultValues: {password: '', confirmPassword: ''},
    validators: {onSubmit: resetPasswordSchema},
    onSubmit: async ({value}) => {
      setServerError(null);
      try {
        await api.post('/auth/reset-password', {
          token,
          password: value.password,
          confirm_password: value.confirmPassword,
        });
        setSuccess(true);
        setTimeout(() => navigate('/login', {replace: true}), 3000);
      } catch (err) {
        if (err instanceof Error && err.message.includes('400')) {
          setTokenValid(false);
        } else {
          setServerError('Something went wrong. Please try again.');
        }
      }
    },
  });

  if (tokenValid === null) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950">
        <p className="text-gray-400 text-sm">Checking your link…</p>
      </div>
    );
  }

  if (!tokenValid) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950">
        <div className="w-full max-w-sm p-8 rounded-2xl bg-gray-900 shadow-xl flex flex-col gap-6">
          <div className="text-center">
            <h1 className="text-3xl font-bold text-white tracking-tight">Lingwa</h1>
            <p className="mt-2 text-gray-400 text-sm">Link invalid or expired</p>
          </div>
          <p className="text-gray-400 text-sm text-center">
            This password reset link is invalid or has expired. Request a new one below.
          </p>
          <Link
            to="/forgot-password"
            className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-colors text-center"
          >
            Request new link
          </Link>
        </div>
      </div>
    );
  }

  if (success) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950">
        <div className="w-full max-w-sm p-8 rounded-2xl bg-gray-900 shadow-xl flex flex-col gap-6">
          <div className="text-center">
            <h1 className="text-3xl font-bold text-white tracking-tight">Lingwa</h1>
            <p className="mt-2 text-gray-400 text-sm">Password updated</p>
          </div>
          <p className="text-gray-400 text-sm text-center">
            Your password has been reset. Redirecting you to sign in…
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950">
      <div className="w-full max-w-sm p-8 rounded-2xl bg-gray-900 shadow-xl flex flex-col gap-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-white tracking-tight">Lingwa</h1>
          <p className="mt-2 text-gray-400 text-sm">Choose a new password</p>
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            e.stopPropagation();
            form.handleSubmit();
          }}
          className="flex flex-col gap-4"
        >
          <form.Field name="password">
            {(field) => (
              <FormField
                field={field}
                label="New password"
                type="password"
                placeholder="Min. 8 characters"
                autoComplete="new-password"
                autoFocus
              />
            )}
          </form.Field>

          <form.Field name="confirmPassword">
            {(field) => (
              <FormField
                field={field}
                label="Confirm new password"
                type="password"
                placeholder="Repeat your password"
                autoComplete="new-password"
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
                {isSubmitting ? 'Saving…' : 'Reset password'}
              </button>
            )}
          </form.Subscribe>
        </form>
      </div>
    </div>
  );
}

export default ResetPasswordPage;
