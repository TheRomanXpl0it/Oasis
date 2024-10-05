import { useLocalStorage } from "@mantine/hooks"



export const useLoginToken = () => {
    return useLocalStorage({
        key: 'access_token',
        defaultValue: null
    })
}