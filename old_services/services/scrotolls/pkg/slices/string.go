package slices

func ContainsString(in []string, needle string) bool {
	for _, e := range in {
		if e == needle {
			return true
		}
	}
	return false
}
