import { Box, Image, Pill, ScrollAreaAutosize, Space, Table, Text, Title } from "@mantine/core"
import { useConfigQuery, useTeamQuery, useTeamSolver } from "../scripts/query"
import { LineChart } from "@mantine/charts"
import { hashedColor } from "../scripts/utils"
import { MdGroups } from "react-icons/md";
import { FaHashtag } from "react-icons/fa6";
import { ImTarget } from "react-icons/im";
import { FaServer } from "react-icons/fa6";
import { ServiceScoreData } from "../components/ServiceScoreData";
import { RoundCounter } from "../components/RoundCounter";
import { useParams } from "react-router-dom";
import { NotFoundContent } from "../components/NotFoundContent";

export const ScoreboardTeamDetail = () => {
    

    const { teamId } = useParams()

    const teamData = useTeamQuery(teamId??"")
    const configData = useConfigQuery()
    const teamSolver = useTeamSolver()
    const services = configData.data?.services.sort()??[]

    const currentTeam = teamSolver(`10.60.${teamId}.1`)

    const series = configData.data?.services.map(service => ({ name: service, color: hashedColor(service) }))??[]
    
    const dataLoaded = teamData.isSuccess && configData.isSuccess
    const rows = teamData.data?.sort((a,b)=>b.round-a.round).map((teamData) => {
        return <Table.Tr key={teamData.round}>
            <Table.Td><Box className="center-flex">{teamData.round}</Box></Table.Td>
            <Table.Td><Box className="center-flex" style={{ width: "100%"}}>
                <Image
                    src={"/images/teams/"+(currentTeam?.image == "" || currentTeam == null ?"oasis-player.png":currentTeam.image)}
                    alt={teamData.score.team}
                    mah={120}
                    maw={120}
                />
            </Box></Table.Td>
            <Table.Td><Box className="center-flex-col">
                <Text>{currentTeam?.name??"Unknown Team"}</Text>
                <Space h="3px" />
                <Pill style={{ backgroundColor: "var(--mantine-color-cyan-filled)", color: "white", fontWeight: "bold" }}>{teamData.score.team}</Pill>
            </Box></Table.Td>
            <Table.Td><Box className="center-flex" style={{ fontWeight: "bolder" }}>{teamData.score.score.toFixed(2)}</Box></Table.Td>
            {services.map((service, i) => <Table.Td key={i}><ServiceScoreData score={teamData.score.services.find(ele => ele.service == service)} /></Table.Td>)}
        </Table.Tr>
    });
    


    return dataLoaded?<Box>
        <Title order={1} mb="60px" mt="xs">{currentTeam?.name} Scoreboard</Title>
        <LineChart
            connectNulls
            data={
                teamData.data?.sort((a,b)=>a.round-b.round).map((round) => ({
                    round: round.round,
                    ...round.score.services.reduce((acc, score) => ({ ...acc, [score.service]: score.final_score.toFixed(2) }), {})
                }))
            }
            dataKey="round"
            yAxisLabel="Points"
            xAxisLabel="Round"
            series={series}
            withLegend
            legendProps={{ verticalAlign: 'bottom' }}
            curveType="linear"
            h={450}
        />

        <RoundCounter />
        <Space h="lg" />
        <ScrollAreaAutosize>
            <Table striped>
                <Table.Thead h={40}>
                    <Table.Tr>
                        <Table.Th style={{ width: "10px"}}>
                            <Box className="center-flex"><FaHashtag size={20} /></Box>
                        </Table.Th>
                        <Table.Th style={{ width: "140px"}}>{/*Image*/}</Table.Th>
                        <Table.Th style={{ width: "fit" }}>
                            <Box className="center-flex">
                                <MdGroups size={26} /><Space w="xs" />Team
                            </Box>
                        </Table.Th>
                        <Table.Th>
                            <Box className="center-flex">
                                <ImTarget size={20} /><Space w="xs" />Score
                            </Box>
                        </Table.Th>
                        {services.map(service => <Table.Th key={service}>
                            <Box className="center-flex" style={{width: "100%"}}>
                                <FaServer size={20} /><Space w="xs" />{service}
                            </Box>
                        </Table.Th>)}
                    </Table.Tr>
                </Table.Thead>
                <Table.Tbody>{rows}</Table.Tbody>
            </Table>
        </ScrollAreaAutosize>

    </Box> : currentTeam == null && configData.isSuccess ?<NotFoundContent />:<Box>Loading...</Box>
}