import {useAuth} from '../../context/auth/useAuth'

export default function DashboardPage() {
  const {user, logout} = useAuth()

  return (
    <div className="min-h-screen bg-gray-950 text-white">
      <header className="flex items-center justify-between px-6 py-4 border-b border-gray-800">
        <h1 className="text-xl font-bold tracking-tight">Lingwa</h1>
        <div className="flex items-center gap-4">
          {user?.avatar_url && (
            <img src={user.avatar_url} alt={user.name ?? ''} className="w-8 h-8 rounded-full" />
          )}
          <span className="text-sm text-gray-300">{user?.name ?? user?.email}</span>
          <button
            onClick={logout}
            className="text-sm text-gray-400 hover:text-white transition-colors"
          >
            Sign out
          </button>
        </div>
      </header>

      <main className="px-6 py-12 max-w-2xl mx-auto">
        <h2 className="text-2xl font-semibold">
          Welcome back{user?.name ? `, ${user.name}` : ''}!
        </h2>
        <p className="mt-2 text-gray-400">Your dashboard is on its way.</p>
      </main>
    </div>
  )
}
