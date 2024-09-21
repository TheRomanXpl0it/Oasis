import { Box, Image, Paper, Pill, ScrollAreaAutosize, Space, Table, Text, Title } from "@mantine/core"
import { useChartQuery, useConfigQuery, useScoreboardQuery, useTeamSolver } from "../scripts/query"
import { ChartTooltipProps, LineChart } from "@mantine/charts"
import { hashedColor } from "../scripts/utils"
import { MdGroups } from "react-icons/md";
import { FaHashtag } from "react-icons/fa6";
import { ImTarget } from "react-icons/im";
import { FaServer } from "react-icons/fa6";
import { ServiceScoreData } from "../components/ServiceScoreData";
import { RoundCounter } from "../components/RoundCounter";
import { useNavigate } from "react-router-dom";

function ChartTooltip({ label, payload }: ChartTooltipProps) {
    if (!payload) return null;
    const teamSolver = useTeamSolver()
    const topTeams = 10
    return (
      <Paper px="md" py="sm" withBorder shadow="md" radius="md" style={{zIndex:2}}>
        <Box>
            <Box style={{ fontWeight: 400 }}>Round {label}</Box>
            <Space h="md" />
                <b>Top {topTeams} Teams:</b>
                {payload.sort((a, b) => parseFloat(b.value) - parseFloat(a.value)).slice(0, topTeams).map((item) => (
                <Box key={item.dataKey}>
                    <span style={{color:item.color}}>{teamSolver(atob(item.name))?.name}</span>: {item.value} points
                </Box>
            ))}
        </Box>
      </Paper>
    );
  }

export const ScoreboardPage = () => {

    const chartData = useChartQuery()
    const scoreboardData = useScoreboardQuery()
    const configData = useConfigQuery()
    const teamSolver = useTeamSolver()
    const navigate = useNavigate()

    const series = configData.data?.teams.sort((a,b) => a.host.localeCompare(b.host)).map(team => ({  label: team.name, color: team.nop?"grey":hashedColor(team.name+team.host), name: btoa(team.host) }))??[]
    const dataLoaded = chartData.isSuccess && scoreboardData.isSuccess && configData.isSuccess
    const rows = scoreboardData.data?.scores.sort((a,b)=>{
        const scoreDiff = b.score-a.score
        if (scoreDiff !== 0) return scoreDiff
        return a.team.localeCompare(b.team)
    }).map((teamData, pos) => {
        const teamInfo = teamSolver(teamData.team)
        return <Table.Tr key={teamData.team} onClick={()=>navigate(`/scoreboard/team/${teamInfo?.id}`)}>
            <Table.Td><Box className="center-flex">{pos + 1}</Box></Table.Td>
            <Table.Td><Box className="center-flex" style={{ width: "100%"}}>
                <Image
                    src={"/images/teams/"+(teamInfo?.image == "" || teamInfo == null ?"oasis-player.png":teamInfo.image)}
                    alt={teamData.team}
                    mah={120}
                    maw={120}
                />
            </Box></Table.Td>
            <Table.Td><Box className="center-flex-col">
                <Text>{teamInfo?.name??"Unknown Team"}</Text>
                <Space h="3px" />
                <Pill style={{ backgroundColor: "var(--mantine-color-cyan-filled)", color: "white", fontWeight: "bold" }}>{teamData.team}</Pill>
            </Box></Table.Td>
            <Table.Td><Box className="center-flex" style={{ fontWeight: "bolder" }}>{teamData.score.toFixed(2)}</Box></Table.Td>
            {teamData.services.map((service, i) => <Table.Td key={i}><ServiceScoreData score={service} /></Table.Td>)}
        </Table.Tr>
    });
    


    return dataLoaded?<Box>
        <Title order={1} mb="60px" mt="xs">Scoreboard</Title>
        <LineChart
            connectNulls
            data={
                chartData.data?.map((round, i) => ({
                    round: i,
                    ...round.scores.reduce((acc, score) => ({ ...acc, [btoa(score.team)]: score.score.toFixed(2) }), {})
                }))
            }
            dataKey="round"
            yAxisLabel="Points"
            xAxisLabel="Round"

            series={series}
            tooltipProps={{
                content: ({ label, payload }) => <ChartTooltip label={label} payload={payload} />
            }}
            withLegend
            legendProps={{ verticalAlign: 'bottom' }}
            curveType="linear"
            h={450}
        />

        <RoundCounter />
        <Space h="lg" />
        <ScrollAreaAutosize>
            <Table highlightOnHover striped>
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
                        {configData.data.services.map(service => <Table.Th key={service}>
                            <Box className="center-flex" style={{width: "100%"}}>
                                <FaServer size={20} /><Space w="xs" />{service}
                            </Box>
                        </Table.Th>)}
                    </Table.Tr>
                </Table.Thead>
                <Table.Tbody>{rows}</Table.Tbody>
            </Table>
        </ScrollAreaAutosize>

    </Box> : <Box>Loading...</Box>
}