package main

import (
	"game/log"
	"net"
	"strings"

	"github.com/pkg/errors"
)

func ctfRouteCommand(cmd string) error {
	conn, err := net.Dial("unix", "/unixsk/ctfroute.sock")
	if err != nil {
		log.Debugf("Failed to connect to the ctf router: %v", err)
		return err
	}
	defer conn.Close()
	heloReceived := false
	for {
		response := make([]byte, 1024)
		read, err := conn.Read(response)
		if err != nil {
			log.Debugf("Failed to read response from the ctf router: %v", err)
			return err
		}
		if read > 0 {
			strippedResponse := strings.Trim(string(response[:read]), "\n ")
			if !heloReceived {
				if strippedResponse == "HELO" {
					heloReceived = true
					_, err = conn.Write([]byte(cmd + "\n"))
					if err != nil {
						log.Debugf("Failed to send data to the ctf router: %v", err)
						return err
					}
					log.Debugf("Sent %v CTF Route command", cmd)
				} else {
					log.Debugf("Failed to %v CTF Route (no HELO): '%s'", cmd, strippedResponse)
					return errors.New("unexpected response (no HELO)")
				}
			} else {
				if strippedResponse == "OK" {
					log.Infof("CTF Route %ved", cmd)
					return nil
				} else {
					log.Debugf("Failed to %v CTF Route (unexpected response): '%s'", cmd, strippedResponse)
					return errors.New("unexpected response")
				}
			}
		}

	}
}

func CtfRouteUnlock() error {
	return ctfRouteCommand("UNLOCK")
}

func CtfRouteLock() error {
	return ctfRouteCommand("LOCK")
}
