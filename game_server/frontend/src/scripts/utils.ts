

export function stringToHash(string:string) {

    let hash = 0;

    if (string.length == 0) return hash;

    for (let i = 0; i < string.length; i++) {
        let char = string.charCodeAt(i);
        hash = ((hash << 5) - hash) + char;
        hash = hash & hash;
    }

    return hash;
}

export const hashedColor = (string:string) => {
    return GRAPH_COLOR_PALETTE[Math.abs(stringToHash(string)) % GRAPH_COLOR_PALETTE.length]
}

export const GRAPH_COLOR_PALETTE = [
    "red", "pink", "grape", "violet", "indigo", "blue", "cyan", "teal", "green", "lime", "yellow", "orange"
]
