import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

export default function Login() {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const navigate = useNavigate();

  const submit = async (e) => {
    e.preventDefault();
    try {
      const url = isLogin ? 'http://localhost:5000/api/login' : 'http://localhost:5000/api/register';
      const { data } = await axios.post(url, { username, password });
      if (isLogin) {
        localStorage.setItem('user', data.username);
        navigate('/dashboard');
      } else {
        alert('Account created! Please login.');
        setIsLogin(true);
      }
    } catch (err) {
      alert(err.response?.data?.error || 'Error connecting to server');
    }
  };

  return (
    <div className="container">
      <h1 style={{ marginTop: '80px' }}>SHOP MANAGEMENT</h1>
      <p className="subtitle">{isLogin ? 'Main Dashboard Login' : 'Create Account'}</p>
      
      <form onSubmit={submit}>
        <input placeholder="Username" value={username} onChange={e => setUsername(e.target.value)} required />
        <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} required />
        <button type="submit" className="btn btn-blue">{isLogin ? 'LOGIN' : 'SIGN UP'}</button>
      </form>
      
      <p style={{ cursor: 'pointer', color: '#3498db', marginTop: '20px' }} onClick={() => setIsLogin(!isLogin)}>
        {isLogin ? "Don't have an account? Create one" : "Already have an account? Login"}
      </p>
      
      <div className="footer">Purva Kavathekar</div>
    </div>
  );
}