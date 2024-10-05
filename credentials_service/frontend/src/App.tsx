import { BrowserRouter as Router, Route, Routes, Navigate} from 'react-router-dom';
import { UserLogin } from './components/UserLogin';
import { UserTeams } from './components/UserTeam';
import { AdminLogin } from './components/AdminLogin';
import { AdminDashboard } from './components/AdminDashboard';
import { useEffect } from 'react';
import { useLoginToken } from './scripts/utils';
import { getIsAdmin } from './scripts/net';

function App() {

    const [token] = useLoginToken()

    useEffect(() => {
        if (!token){
            if (!["/user", "/admin"].includes(window.location.pathname)){
                if (getIsAdmin()){
                    location.href = "/admin";
                }else{
                    location.href = "/user";
                }
            }
        }
    }, [token]);

    return (
        <Router>
            <Routes>
                <Route path="/" element={<Navigate to={getIsAdmin()?"/admin":"/user"} replace />} />
                {/* Rotta per il login utente */}
                <Route path="/user" element={<UserLogin />} />
                {/* Rotta per la visualizzazione del team */}
                <Route path="/user/team" element={<UserTeams />} />
                {/* Rotta per il login admin */}
                <Route path="/admin" element={<AdminLogin />} />
                {/* Rotta per la dashboard dell'admin */}
                <Route path="/admin/dashboard" element={<AdminDashboard />} />
            </Routes>
        </Router>
    );
}

export default App;
