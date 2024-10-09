import { useState, useEffect } from 'react';
import { downloadConfig, fetchUserTeam, UserTeam } from '../scripts/net';
import { ActionIcon, Alert, Box, Button, Container, CopyButton, Paper, Space, Table, TableData, Text, Title, Tooltip } from '@mantine/core';
import { FaRegCopy } from "react-icons/fa";
import { FaCheck } from "react-icons/fa6";
import { useLoginToken } from '../scripts/utils';
import { IoLogOut } from "react-icons/io5";

export const UserTeams = () => {
    const [team, setTeam] = useState<UserTeam|null>(null);
    const [message, setMessage] = useState({
        message: '',
        error: false,
    });

    useEffect(() => {
        fetchUserTeam()
            .then(data => setTeam(data))
            .catch(error => setMessage(error));
    }, []);

    const handleDownload = () => {
        setMessage({
            message: '',
            error: false,
        });
        downloadConfig(`team${team?.id}-${team?.profile}.conf`).then(() => {
            setMessage({
                message:'Configuration downloaded',
                error: false,
            })
        }).catch(err => {
            setMessage({
                message: err,
                error: true,
            });
        });
    };
    const [_, setToken] = useLoginToken()

    if (!team) {
        return <Box>Loading...</Box>;
    }

    const tableData: TableData = {
        head: ['Team ID', 'Profile No.', 'Server IP'],
        body: [
            [team.id, team.profile, `10.60.${team.id}.1`]
        ],
      };

    return <Container size="sm" className='center-flex' style={{flex: 1}}>
        <Paper bg="dark" p={30} radius={10} style={{ flex: 1 }}>
            <Box className='center-flex'>
                <Title order={1}>Team Info - {team.team_name}</Title>
                <Box style={{flex: 1}} />
                <ActionIcon color='red' variant='light' onClick={() => setToken(null)} size="lg"><IoLogOut size={20} /></ActionIcon>
            </Box>
            <Table data={tableData} my={15} />
            <Box className='center-flex' my={15}>
                <Text><strong>Token (and VM password): </strong>{team.token}</Text>
                <CopyButton value={team.token} timeout={2000}>
                {({ copied, copy }) => (
                    <Tooltip label={copied ? 'Copied' : 'Copy'} withArrow position="right">
                    <ActionIcon color={copied ? 'teal' : 'gray'} variant="subtle" onClick={copy}>
                        {copied ? <FaCheck /> : <FaRegCopy /> }
                    </ActionIcon>
                    </Tooltip>
                )}
                </CopyButton>
            </Box>
            <Space h="md" />
            <Button onClick={handleDownload}>Download Configuration</Button>
            <Space h="md" />
            {message.message && <Alert color={message.error ? 'red' : 'teal'}>{message.message}</Alert>}
        </Paper>
    </Container>
}

