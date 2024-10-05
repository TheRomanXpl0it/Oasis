
export type Team = {
    id: number,
    name: string,
    pins: {
        pin: string,
        profile: number
    }[],
    token: string,
    wireguard_port: number,
    nop: number,
}

export type UserTeam = {
    id: number,
    team_name: string,
    wireguard_port: number,
    profile: number,
    token: string,
    nop: boolean
}

export type PinResponse = {
    pin: string,
}

export type LoginInfo = {
    access_token: string
}

const getUrl = (path: string) => {
    const prefix = import.meta.env.DEV ? "http://localhost:1234/api" : "/api"
    return prefix + path
}

export const getToken = () => {
    return JSON.parse(localStorage.getItem('access_token')??"null");
}

export const setToken = (token: string) => {
    localStorage.setItem('access_token', JSON.stringify(token));
}

export const setIsAdmin = (isAdmin: boolean) => {
    localStorage.setItem('is_admin', JSON.stringify(isAdmin));
}

export const getIsAdmin = () => {
    return JSON.parse(localStorage.getItem('is_admin')??"false");
}

const checkUnauthorized = (response: Response) => {
    if (response.status === 401) {
        localStorage.removeItem('access_token');
        location.href = '/user';
        throw 'Session expired. Please login again.';
    }
    if (response.status === 422) {
        localStorage.removeItem('access_token');
        location.href = '/user';
        throw 'Invalid Login. Please try again.';
    }
}

export const fetchTeams = async () => {
    const response = await fetch(getUrl('/admin/teams'), {
        headers: {
            'Authorization': `Bearer ${getToken()}`,
        },
    }).catch(err => {
        console.error(err);
        throw 'Network error. Please try again.';
    });

    if (response.ok) {
        return (await response.json()) as Team[];
    } else {
        checkUnauthorized(response);
        const errorText = await response.text();
        throw errorText;
    }
};

export const fetchUserTeam = async () => {
    const response = await fetch(getUrl('/user/team'), {
        headers: {
            'Authorization': `Bearer ${getToken()}`,
        },
    }).catch(err => {
        console.error(err);
        throw 'Network error. Please try again.';
    });

    if (response.ok) {
        return (await response.json()) as UserTeam;
    } else {
        checkUnauthorized(response);
        const errorText = await response.text();
        throw errorText;
    }
}

export const adminLogin = async (token: string) => {
    const response = await fetch(getUrl('/admin/login'), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ token }),
    }).catch(err => {
        console.error(err);
        throw 'Network error. Please try again.';
    });

    if (response.ok) {
        const data = (await response.json()) as LoginInfo;
        setToken(data.access_token);
        setIsAdmin(true);
        return data;
    } else {
        const result = await response.json();
        throw result.msg || 'Login failed. Please try again.';
    }
}

export const userLogin = async (pin: string) => {
    const response = await fetch(getUrl('/user/login'), {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ pin }),
    }).catch(err => {
        console.error(err);
        throw 'Network error. Please try again.';
    });

    if (response.ok) {
        const data = (await response.json()) as LoginInfo;
        setToken(data.access_token);
        setIsAdmin(false);
        return data;
    } else {
        const result = await response.json();
        throw result.msg || 'Invalid PIN. Please try again.';
    }
}

export const downloadConfig = async () => {
    const response = await fetch(getUrl('/user/download_config/'), {
        headers: { 'Authorization': `Bearer ${getToken()}` },
    });
    if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'oasis-vpn-profile.conf';
        a.click();
        return true;
    } else {
        checkUnauthorized(response);
        const data = await response.json();
        throw data.msg || 'Download failed. Please try again.';
    }
}