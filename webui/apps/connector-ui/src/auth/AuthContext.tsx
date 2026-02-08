import { createContext, useContext } from "react";
import type { AuthStatus } from "../api/types";

export type AuthState = {
  authStatus: AuthStatus | null;
  permissions: string[];
  can: {
    read: boolean;
    write: boolean;
    configure: boolean;
    start_stop: boolean;
    delete: boolean;
    manage_users: boolean;
  };
  loading: boolean;
};

const Ctx = createContext<AuthState | null>(null);

export function AuthProvider(props: { value: AuthState; children: React.ReactNode }) {
  return <Ctx.Provider value={props.value}>{props.children}</Ctx.Provider>;
}

export function useAuthState(): AuthState {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAuthState must be used within AuthProvider");
  return v;
}

