package log

import (
	"os"
	"strings"

	"github.com/op/go-logging"
)

const (
	END = "\033[0m"

	BLACK  = "\033[30m"
	RED    = "\033[31m"
	GREEN  = "\033[32m"
	YELLOW = "\033[33m"
	BLUE   = "\033[34m"
	PURPLE = "\033[35m"
	CYAN   = "\033[36m"
	GREY   = "\033[90m"

	HIGH_RED    = "\033[91m"
	HIGH_GREEN  = "\033[92m"
	HIGH_YELLOW = "\033[93m"
	HIGH_BLUE   = "\033[94m"
	HIGH_PURPLE = "\033[95m"
	HIGH_CYAN   = "\033[96m"
)

var Logger = logging.MustGetLogger("logger")

var fileFormat = logging.MustStringFormatter(
	`%{time:15:04:05.000} %{level:.8s} ▶ %{message}`,
)
var backendFormat = logging.MustStringFormatter(
	`%{color}%{time:15:04:05.000} %{level:.8s} ▶%{color:reset} %{message}`,
)

var (
	backends []logging.Backend
	logFile  *os.File
)

func init() {
	backends = make([]logging.Backend, 0, 1)

	backend := logging.NewLogBackend(os.Stdin, "", 0)
	backendFormatter := logging.NewBackendFormatter(backend, backendFormat)
	backendLeveled := logging.AddModuleLevel(backendFormatter)
	backendLeveled.SetLevel(logging.INFO, "")

	backends = append(backends, backendLeveled)
	logging.SetBackend(backends...)

	filebackend := logging.NewLogBackend(os.Stderr, "", 0)
	filebackendFormatter := logging.NewBackendFormatter(filebackend, fileFormat)
	filebackendLeveled := logging.AddModuleLevel(filebackendFormatter)
	filebackendLeveled.SetLevel(logging.INFO, "")

	backends = append(backends, filebackendLeveled)
	logging.SetBackend(backends...)
}

func CloseLogFile() {
	logFile.Close()
}

func SetLogLevel(newLevel string) {
	var level logging.Level
	lev := strings.ToLower(newLevel)
	switch lev {
	case "debug":
		level = logging.DEBUG
	default:
		fallthrough
	case "info":
		level = logging.INFO
	case "notice":
		level = logging.NOTICE
	case "warning":
		level = logging.WARNING
	case "error":
		level = logging.ERROR
	case "critical":
		level = logging.CRITICAL
	}
	logging.SetLevel(level, "")
}

func Debug(args ...interface{}) {
	Logger.Debug(args...)
}

func Debugf(format string, args ...interface{}) {
	Logger.Debugf(format, args...)
}

func Info(args ...interface{}) {
	Logger.Info(args...)
}

func Infof(format string, args ...interface{}) {
	Logger.Infof(format, args...)
}

func Notice(args ...interface{}) {
	Logger.Notice(args...)
}

func Noticef(format string, args ...interface{}) {
	Logger.Noticef(format, args...)
}

func Warning(args ...interface{}) {
	Logger.Warning(args...)
}

func Warningf(format string, args ...interface{}) {
	Logger.Warningf(format, args...)
}

func Error(args ...interface{}) {
	Logger.Error(args...)
}

func Errorf(format string, args ...interface{}) {
	Logger.Errorf(format, args...)
}

func Critical(args ...interface{}) {
	Logger.Critical(args...)
}

func Criticalf(format string, args ...interface{}) {
	Logger.Criticalf(format, args...)
}

func Fatal(args ...interface{}) {
	Logger.Fatal(args...)
}

func Fatalf(format string, args ...interface{}) {
	Logger.Fatalf(format, args...)
}

func Panic(args ...interface{}) {
	Logger.Panic(args...)
}

func Panicf(format string, args ...interface{}) {
	Logger.Panicf(format, args...)
}
