package httputil

type Header string
type MIMEType string

const (
	HeaderContentType   Header   = "Content-Type"
	HeaderContentLength Header   = "Content-Length"
	TypeApplicationJSON MIMEType = "application/json"
	TypeTextPlain       MIMEType = "text/plain"
)
