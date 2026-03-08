import {useEffect, useRef} from 'react';
import {useNavigate, useSearchParams} from 'react-router-dom';
import {useAuth} from '../../context/auth/useAuth';

export default function AuthCallbackPage() {
  const [searchParams] = useSearchParams();
  const {login} = useAuth();
  const navigate = useNavigate();
  const called = useRef(false);

  useEffect(() => {
    if (called.current) return;
    called.current = true;

    const token = searchParams.get('token');
    if (!token) {
      navigate('/login', {replace: true});
      return;
    }

    login(token)
      .then(() => navigate('/dashboard', {replace: true}))
      .catch(() => navigate('/login', {replace: true}));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950">
      <p className="text-gray-400 text-sm">Signing you in…</p>
    </div>
  );
}
