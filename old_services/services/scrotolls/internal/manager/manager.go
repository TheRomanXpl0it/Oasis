package manager

import (
	userstorage "github.com/HackerDom/ructfe2020/internal/storage/users"
	"github.com/HackerDom/ructfe2020/internal/storage/docs"
	"github.com/HackerDom/ructfe2020/internal/storage/sessions"
)

type Manager struct {
	*users
	*documents
}

func New(usersStorage userstorage.Users, documentsStorage docs.Documents, sessStorage sessions.Sessions) *Manager {
	return &Manager{
		&users{usersStorage, sessStorage},
		&documents{documentsStorage, usersStorage},
	}
}
