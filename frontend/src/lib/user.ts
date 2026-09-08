const USER_ID_KEY = "chunky-user-id";

export function getUserId(): string {
  const existing = window.localStorage.getItem(USER_ID_KEY);
  if (existing) {
    return existing;
  }
  const created = crypto.randomUUID();
  window.localStorage.setItem(USER_ID_KEY, created);
  return created;
}
