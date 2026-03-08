import {useState} from 'react';
import {useNavigate, Link} from 'react-router-dom';
import {api} from '../../api/client';
import {useAppForm} from '../../hooks/useAppForm';
import {FormField} from '../../components/ui/FormField';
import {signUpSchema, type SignUpValues} from '../../schemas/auth';

export function SignUpPage() {
  const navigate = useNavigate();
  const [submitted, setSubmitted] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const form = useAppForm({
    defaultValues: {email: ''},
    validators: {onSubmit: signUpSchema},
    onSubmit: async ({value}: {value: SignUpValues}) => {
      setServerError(null);
      try {
        await api.post('/auth/register', {email: value.email});
        setSubmitted(true);
      } catch (err) {
        if (err instanceof Error && err.message.includes('409')) {
          setServerError('An account with this email already exists.');
        } else {
          setServerError('Something went wrong. Please try again.');
        }
      }
    },
  });

  if (submitted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950">
        <div className="w-full max-w-sm p-8 rounded-2xl bg-gray-900 shadow-xl flex flex-col gap-4 text-center">
          <h1 className="text-2xl font-bold text-white">Check your email</h1>
          <p className="text-gray-400 text-sm">
            We sent a verification link to{' '}
            <span className="text-white">{form.state.values.email}</span>. Click it to finish
            setting up your account.
          </p>
          <button
            onClick={() => navigate('/login')}
            className="mt-2 text-indigo-400 hover:text-indigo-300 text-sm"
          >
            Back to sign in
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950">
      <div className="w-full max-w-sm p-8 rounded-2xl bg-gray-900 shadow-xl flex flex-col gap-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-white tracking-tight">Lingwa</h1>
          <p className="mt-2 text-gray-400 text-sm">Create your account</p>
        </div>

        <a
          href={`${import.meta.env.VITE_API_URL}/auth/google/login`}
          className="w-full flex items-center justify-center gap-3 px-4 py-3 rounded-lg bg-white text-gray-800 font-medium text-sm hover:bg-gray-100 transition-colors"
        >
          <GoogleIcon />
          Continue with Google
        </a>

        <div className="flex items-center gap-3">
          <div className="flex-1 h-px bg-gray-700" />
          <span className="text-gray-500 text-xs">or</span>
          <div className="flex-1 h-px bg-gray-700" />
        </div>

        <form
          onSubmit={(e) => {
            e.preventDefault();
            e.stopPropagation();
            form.handleSubmit();
          }}
          className="flex flex-col gap-4"
        >
          <form.Field name="email">
            {(field) => (
              <FormField
                field={field}
                label="Email"
                type="email"
                placeholder="you@example.com"
                autoComplete="email"
              />
            )}
          </form.Field>

          {serverError && <p className="text-red-400 text-sm">{serverError}</p>}

          <form.Subscribe>
            {(state) => (
              <button
                type="submit"
                disabled={state.isSubmitting}
                className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-sm transition-colors"
              >
                {state.isSubmitting ? 'Sending…' : 'Continue with email'}
              </button>
            )}
          </form.Subscribe>
        </form>

        <p className="text-center text-sm text-gray-400">
          Already have an account?{' '}
          <Link to="/login" className="text-indigo-400 hover:text-indigo-300">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}

export default SignUpPage;

function GoogleIcon() {
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" xmlns="http://www.w3.org/2000/svg">
      <path
        d="M17.64 9.2c0-.637-.057-1.251-.164-1.84H9v3.481h4.844c-.209 1.125-.843 2.078-1.796 2.717v2.258h2.908c1.702-1.567 2.684-3.875 2.684-6.615z"
        fill="#4285F4"
      />
      <path
        d="M9 18c2.43 0 4.467-.806 5.956-2.184l-2.908-2.258c-.806.54-1.837.86-3.048.86-2.344 0-4.328-1.584-5.036-3.711H.957v2.332A8.997 8.997 0 0 0 9 18z"
        fill="#34A853"
      />
      <path
        d="M3.964 10.707A5.41 5.41 0 0 1 3.682 9c0-.593.102-1.17.282-1.707V4.961H.957A8.996 8.996 0 0 0 0 9c0 1.452.348 2.827.957 4.039l3.007-2.332z"
        fill="#FBBC05"
      />
      <path
        d="M9 3.58c1.321 0 2.508.454 3.44 1.345l2.582-2.58C13.463.891 11.426 0 9 0A8.997 8.997 0 0 0 .957 4.961L3.964 7.293C4.672 5.163 6.656 3.58 9 3.58z"
        fill="#EA4335"
      />
    </svg>
  );
}
