import {Navigate} from 'react-router-dom';
import {useAuth} from '../../context/auth/useAuth';

export default function ProtectedRoute({children}: {children: React.ReactNode}) {
  const {user, isLoading} = useAuth();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-950">
        <p className="text-gray-400 text-sm">Loading…</p>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return <>{children}</>;
}
