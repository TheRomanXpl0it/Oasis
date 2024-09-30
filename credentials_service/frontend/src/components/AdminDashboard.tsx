import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { fetchTeams, Team } from '../scripts/net';
import { Accordion, ActionIcon, Alert, Box, Container, Paper, ScrollAreaAutosize, Space, Title } from '@mantine/core';
import { useLoginToken } from '../scripts/utils';
import { IoLogOut } from 'react-icons/io5';
import { FaArrowRight, FaArrowLeft } from "react-icons/fa";

export const AdminDashboard = () => {
    const [teams, setTeams] = useState<Team[]>([]);
    const [message, setMessage] = useState({
        message: '',
        error: false,
    });
    const navigate = useNavigate();

    useEffect(() => {
        fetchTeams()
            .then(data => setTeams(data))
            .catch(error => setMessage({
                message: error,
                error: true
            }));
    }, [navigate]);

    const [_, setToken] = useLoginToken()

    const [shownProfile, setShownProfile] = useState(0);


    if (!teams) {
        return <Box>Loading...</Box>;
    }

    const items = teams.map((item) => (
        <Accordion.Item key={item.id} value={`team${item.id}`}>
          <Accordion.Control onClick={() => setShownProfile(0)} style={{ userSelect: "none" }}>{item.name}</Accordion.Control>
          <Accordion.Panel py={40}>
            <Box className='center-flex-col'>
                <small style={{ userSelect: "none" }}>Profile {shownProfile+1}</small>
                <Box className='center-flex' style={{ flex: 1, width: "100%" }}>
                    <FaArrowLeft onClick={() => setShownProfile(shownProfile == 0?shownProfile:(shownProfile - 1) % item.pins.length)} size={25} cursor="pointer"/>
                    <Box style={{flex: 1}} />
                    <Title order={1} style={{ userSelect: "none" }}>{item.pins[shownProfile].pin}</Title>
                    <Box style={{flex: 1}} />
                    <FaArrowRight onClick={() => setShownProfile((shownProfile == item.pins.length-1?shownProfile:shownProfile + 1) % item.pins.length)} size={25} cursor="pointer"/>
                </Box>
            </Box>
            </Accordion.Panel>
        </Accordion.Item>
      ));

    return <Container size="sm" className='center-flex' style={{flex: 1}}>
        <Paper bg="dark" p={30} radius={10} style={{ flex: 1 }}>
            <ScrollAreaAutosize display="block" mah="90vh">
                <Box className='center-flex'>
                    <Title order={1}>Admin Dashboard</Title>
                    <Box style={{flex: 1}} />
                    <ActionIcon color='red' variant='light' onClick={() => setToken(null)} size="lg"><IoLogOut size={20} /></ActionIcon>
                </Box>
                <Space h="md" />
                <Accordion defaultValue="Apples">
                    {items}
                </Accordion>
                <Space h="md" />
                {message.message && <Alert color={message.error ? 'red' : 'teal'}>{message.message}</Alert>}
            </ScrollAreaAutosize>
        </Paper>
    </Container>
}

