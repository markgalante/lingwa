import {useState} from 'react';
import {Link} from 'react-router-dom';
import {api} from '../../api/client';
import {useAppForm} from '../../hooks/useAppForm';
import {FormField} from '../../components/ui/FormField';
import {forgotPasswordSchema} from '../../schemas/auth';

export function ForgotPasswordPage() {
  const [sent, setSent] = useState(false);
  const [serverError, setServerError] = useState<string | null>(null);

  const form = useAppForm({
    defaultValues: {email: ''},
    validators: {onSubmit: forgotPasswordSchema},
    onSubmit: async ({value}) => {
      setServerError(null);
      try {
        await api.post('/auth/forgot-password', {email: value.email});
        setSent(true);
      } catch {
        setServerError('Something went wrong. Please try again.');
      }
    },
  });

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950">
      <div className="w-full max-w-sm p-8 rounded-2xl bg-gray-900 shadow-xl flex flex-col gap-6">
        <div className="text-center">
          <h1 className="text-3xl font-bold text-white tracking-tight">Lingwa</h1>
          <p className="mt-2 text-gray-400 text-sm">
            {sent ? 'Check your email' : 'Forgot your password?'}
          </p>
        </div>

        {sent ? (
          <div className="flex flex-col gap-4">
            <p className="text-gray-400 text-sm text-center">
              If an account exists for <span className="text-white">{form.state.values.email}</span>
              , we sent a password reset link. Check your inbox.
            </p>
            <Link
              to="/login"
              className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-colors text-center"
            >
              Back to sign in
            </Link>
          </div>
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
              Enter your email and we'll send you a link to reset your password.
            </p>

            <form.Field name="email">
              {(field) => (
                <FormField
                  field={field}
                  label="Email"
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
                  {isSubmitting ? 'Sending…' : 'Send reset link'}
                </button>
              )}
            </form.Subscribe>

            <p className="text-center text-sm text-gray-400">
              <Link to="/login" className="text-indigo-400 hover:text-indigo-300">
                Back to sign in
              </Link>
            </p>
          </form>
        )}
      </div>
    </div>
  );
}

export default ForgotPasswordPage;
