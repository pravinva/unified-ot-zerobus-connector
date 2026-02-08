import { createContext, useContext } from "react";

export type ToastKind = "ok" | "warn" | "bad";
export type ToastApi = { show: (message: string, kind?: ToastKind) => void };

const Ctx = createContext<ToastApi | null>(null);

export function ToastProvider(props: { api: ToastApi; children: React.ReactNode }) {
  return <Ctx.Provider value={props.api}>{props.children}</Ctx.Provider>;
}

export function useAppToast(): ToastApi {
  const v = useContext(Ctx);
  if (!v) throw new Error("useAppToast must be used within ToastProvider");
  return v;
}

