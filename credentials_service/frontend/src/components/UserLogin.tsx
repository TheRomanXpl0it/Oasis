import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Alert, Button, Container, Group, Paper, PinInput, Space, Title } from '@mantine/core';
import { useForm } from '@mantine/form';
import { userLogin } from '../scripts/net';
import { useLoginToken } from '../scripts/utils';

export const UserLogin = () => {
    const [error, setError] = useState('');
    const navigate = useNavigate();

    const form = useForm({
        initialValues: { pin: '' },
        validate: {
            pin: (value) => value.length != 6 ? 'Invalid Pin' : null,
        },
    });

    const [token] = useLoginToken()

    const [loading, setLoading] = useState(false);

    useEffect(() => {
        if (token){
            navigate('/user/team');
        }
    },[token, navigate]);



    return <Container size="sm" className='center-flex' style={{flex: 1}}>
        <Paper bg="dark" p={30} radius={10} style={{ flex: 1 }}>
            <Title order={1}>Insert your pin:</Title>
            <Space h="md" />
            <form onSubmit={form.onSubmit((data) => {
                setLoading(true);
                userLogin(data.pin)
                    .then(_ => navigate('/user/team'))
                    .catch(err => setError(err))
                    .finally(() => setLoading(false));
            })}>
                <PinInput
                    size="md"
                    length={6}
                    type="number"
                    {...form.getInputProps('pin')}
                />
                <Space h="sm" />
                <Group justify="flex-end" mt="md">
                    <Button type="submit" loading={loading}>Login</Button>
                </Group>
            </form>
            <Space h="md" />
            {error && <Alert color='red'>{error}</Alert>}
        </Paper>
    </Container>
}
