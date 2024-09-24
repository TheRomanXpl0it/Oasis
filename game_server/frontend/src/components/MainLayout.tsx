import { AppShell, Box, Button, Container, Image, Loader, Space, Title } from "@mantine/core"
import { Link } from "react-router-dom"
import { RulesContent } from "../pages/RulesContent"
import { ScoreboardPage } from "../pages/ScoreboardPage"
import { ScoreboardTeamDetail } from "../pages/ScoreboardTeamDetail"
import { useConfigQuery } from "../scripts/query"
import { useEffect, useState } from "react"
import { useQueryClient } from "@tanstack/react-query"
import { NotFoundContent } from "./NotFoundContent"

type Pages = "rules" | "scoreboard" | "scoreboard-team" | "not-found" | "loading"

export const MainLayout = ({ page }: { page:Pages }) => {
    const config = useConfigQuery()
    const [oldRound, setOldRound] = useState(-1)
    const queryClient = useQueryClient()

    useEffect(()=>{
        if (!config.isFetching && oldRound != config.data?.current_round) {
            setOldRound(config.data?.current_round??-1)
            queryClient.invalidateQueries({
                queryKey: ["scoreboard"]
            })
        }
    }, [config.isFetching])

    return <AppShell
        header={{ height: 60 }}
        padding="md"
    >
    <AppShell.Header>
      <Box className='center-flex' style={{ height: "100%" }} >
        <Space w="md" />
        <Image src="/logo.png" alt="Oasis Logo" width={40} height={40} />
        <Title ml="5px" order={2}>
          Oasis
        </Title>
        <Box flex={1} />
        <Box className="center-flex">
          <Title order={5}>
            <Link to="/rules">
                <Button color="cyan" variant={page == "rules"?"filled":"outline"}>
                    Rules
                </Button>
            </Link>
          </Title>
          <Space w="md" />
          <Title order={5}>
            <Link to="/scoreboard">
                <Button color="cyan" variant={page == "scoreboard"?"filled":"outline"}>
                    Scoreboard
                </Button>
            </Link>
          </Title>
          <Space w="md" />
        </Box>
      </Box>
    </AppShell.Header>
    <AppShell.Main>
        <Container size="xl">
            {
                page == "not-found" ? <NotFoundContent />:
                page == "rules" ? <RulesContent /> :
                page == "scoreboard" ? <ScoreboardPage /> :
                page == "scoreboard-team" ? <ScoreboardTeamDetail /> :
                <Box className="center-flex-col" style={{ minHeight: "300px" }}>
                    <Title order={1}>Loading...</Title>
                    <Space h="lg" />
                    <Loader size={40} />
                </Box> 
            }
        </Container>
    </AppShell.Main>
  </AppShell> 
}