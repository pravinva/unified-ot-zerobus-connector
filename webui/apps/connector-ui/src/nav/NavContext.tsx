import { createContext, useContext } from "react";

export type NavigateApi = { go: (key: string) => void };

const Ctx = createContext<NavigateApi | null>(null);

export function NavProvider(props: { api: NavigateApi; children: React.ReactNode }) {
  return <Ctx.Provider value={props.api}>{props.children}</Ctx.Provider>;
}

export function useNav(): NavigateApi {
  const v = useContext(Ctx);
  if (!v) throw new Error("useNav must be used within NavProvider");
  return v;
}

