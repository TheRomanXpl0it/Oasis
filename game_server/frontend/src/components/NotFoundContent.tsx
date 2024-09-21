import { Box, Button, Space, Title } from "@mantine/core"
import { Link } from "react-router-dom"


export const NotFoundContent = () => {
    return <Box className="center-flex-col" style={{ minHeight: "300px" }}>
        <Title order={1}>This page cannot be found</Title>
        <Space h="lg" />
        <Button color="cyan" component={Link} to="/">Go to the home page</Button>
    </Box>
}