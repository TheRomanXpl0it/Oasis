import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { adminLogin } from '../scripts/net';
import { Alert, Button, Container, Group, Paper, PasswordInput, Space, Title } from '@mantine/core';
import { useForm } from '@mantine/form';
import { useLoginToken } from '../scripts/utils';

export const AdminLogin = () => {
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const form = useForm({
        initialValues: { token: '' },
        validate: {
            token: (value) => value.length < 1 ? 'Token is required' : null,
        },
    });

    const [token] = useLoginToken()
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (token){
            navigate('/admin/dashboard');
        }
    },[token, navigate]);

    return <Container size="sm" className='center-flex' style={{flex: 1}}>
        <Paper bg="dark" p={30} radius={10} style={{ flex: 1 }}>
            <Title order={1}>Admin Login</Title>
            <Space h="md" />
            <form onSubmit={form.onSubmit((data) => {
                setLoading(true);
                adminLogin(data.token)
                    .then(_ => navigate('/admin/dashboard'))
                    .catch(err => setError(err))
                    .finally(() => setLoading(false));
            })}>
                <PasswordInput
                    label="Token:"
                    {...form.getInputProps('token')}
                    required
                />
                <Space h="md" />
                <Group justify="flex-end" mt="md">
                    <Button type="submit" loading={loading}>Login</Button>
                </Group>
            </form>
            <Space h="md" />
            {error && <Alert color='red'>{error}</Alert>}
        </Paper>
    </Container>
}
