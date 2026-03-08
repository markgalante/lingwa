import {useState} from 'react'
import {useNavigate, useSearchParams, Link} from 'react-router-dom'
import {api} from '../../api/client'
import {useAuth} from '../../context/auth/useAuth'

interface TokenResponse {
  access_token: string
}

type Step = 'name' | 'password'

export default function VerifyEmailPage() {
  const [searchParams] = useSearchParams()
  const {login} = useAuth()
  const navigate = useNavigate()

  const token = searchParams.get('token')

  const [step, setStep] = useState<Step>('password')
  const [name, setName] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950">
        <div className="w-full max-w-sm p-8 rounded-2xl bg-gray-900 shadow-xl flex flex-col gap-4 text-center">
          <h1 className="text-2xl font-bold text-white">Invalid link</h1>
          <p className="text-gray-400 text-sm">This verification link is invalid or has expired.</p>
          <Link to="/signup" className="text-indigo-400 hover:text-indigo-300 text-sm">
            Start over
          </Link>
        </div>
      </div>
    )
  }

  function handlePasswordSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }
    setError(null)
    setStep('name')
  }

  async function handleNameSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError(null)
    setIsLoading(true)
    try {
      const {access_token} = await api.post<TokenResponse>('/auth/complete-registration', {
        token,
        name: name.trim(),
        password,
        confirm_password: confirmPassword,
      })
      await login(access_token)
      navigate('/dashboard', {replace: true})
    } catch (err) {
      if (err instanceof Error && err.message.includes('400')) {
        setError('This verification link is invalid or has expired.')
      } else {
        setError('Something went wrong. Please try again.')
      }
    } finally {
      setIsLoading(false)
    }
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
          <form onSubmit={handlePasswordSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="password" className="text-sm text-gray-300">Password</label>
              <input
                id="password"
                type="password"
                required
                autoFocus
                autoComplete="new-password"
                minLength={8}
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="w-full px-3 py-2.5 rounded-lg bg-gray-800 border border-gray-700 text-white text-sm placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                placeholder="Min. 8 characters"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <label htmlFor="confirm-password" className="text-sm text-gray-300">Confirm password</label>
              <input
                id="confirm-password"
                type="password"
                required
                autoComplete="new-password"
                minLength={8}
                value={confirmPassword}
                onChange={e => setConfirmPassword(e.target.value)}
                className="w-full px-3 py-2.5 rounded-lg bg-gray-800 border border-gray-700 text-white text-sm placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                placeholder="Repeat your password"
              />
            </div>

            {error && <p className="text-red-400 text-sm">{error}</p>}

            <button
              type="submit"
              className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-colors"
            >
              Continue
            </button>
          </form>
        ) : (
          <form onSubmit={handleNameSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <label htmlFor="name" className="text-sm text-gray-300">Full name</label>
              <input
                id="name"
                type="text"
                required
                autoFocus
                autoComplete="name"
                value={name}
                onChange={e => setName(e.target.value)}
                className="w-full px-3 py-2.5 rounded-lg bg-gray-800 border border-gray-700 text-white text-sm placeholder-gray-500 focus:outline-none focus:border-indigo-500"
                placeholder="Your name"
              />
            </div>

            {error && <p className="text-red-400 text-sm">{error}</p>}

            <div className="flex flex-col gap-2">
              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 text-white font-medium text-sm transition-colors"
              >
                {isLoading ? 'Creating account…' : 'Create account'}
              </button>
              <button
                type="button"
                onClick={() => {setStep('password'); setError(null)}}
                className="text-gray-500 hover:text-gray-400 text-sm"
              >
                Back
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  )
}
