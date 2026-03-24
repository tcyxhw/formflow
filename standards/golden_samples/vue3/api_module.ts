export interface UserDTO {
  id: string
  username: string
}

export async function fetchUser(id: string): Promise<UserDTO> {
  const res = await fetch(`/api/users/${id}`)
  if (!res.ok) {
    throw new Error('Failed to fetch user')
  }
  return res.json()
}
