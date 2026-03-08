import {useState} from 'react';
import {useNavigate, Link} from 'react-router-dom';
import {api} from '../../api/client';
import {useAuth} from '../../context/auth/useAuth';
import {useAppForm} from '../../hooks/useAppForm';
import {FormField} from '../../components/ui/FormField';
import {loginSchema, type LoginValues} from '../../schemas/auth';
interface TokenResponse {
  access_token: string;
}

export function LoginPage() {
  const {login} = useAuth();
  const navigate = useNavigate();
  const [serverError, setServerError] = useState<string | null>(null);

  const form = useAppForm({
    defaultValues: {email: '', password: ''},
    validators: {onSubmit: loginSchema},
    onSubmit: async ({value}: {value: LoginValues}) => {
      setServerError(null);
      try {
        const {access_token} = await api.post<TokenResponse>('/auth/login', {
          email: value.email,
          password: value.password,
        });
        await login(access_token);
        navigate('/dashboard', {replace: true});
      } catch {
        setServerError('Invalid email or password.');
      }
    },
  });

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950">
      <div className="w-full max-w-sm p-8 rounded-2xl bg-gray-900 shadow-xl flex flex-col gap-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-white tracking-tight">Lingwa</h1>
          <p className="mt-2 text-gray-400 text-sm">Welcome back</p>
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

          <form.Field name="password">
            {(field) => (
              <FormField
                field={field}
                label="Password"
                type="password"
                placeholder="••••••••"
                autoComplete="current-password"
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
                {isSubmitting ? 'Signing in…' : 'Sign in'}
              </button>
            )}
          </form.Subscribe>
        </form>

        <p className="text-center text-sm text-gray-400">
          No account?{' '}
          <Link to="/signup" className="text-indigo-400 hover:text-indigo-300">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}

export default LoginPage;

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
