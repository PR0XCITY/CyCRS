import { useSyncExternalStore } from "react";
import { STORAGE_EVENT } from "@/lib/events";

function subscribe(cb: () => void) {
  window.addEventListener("storage", cb);
  window.addEventListener(STORAGE_EVENT, cb);
  return function unsubscribe() {
    window.removeEventListener("storage", cb);
    window.removeEventListener(STORAGE_EVENT, cb);
  };
}

function serverSnapshot() {
  return undefined;
}

function noop() {
  return function unsubscribe() {};
}

function clientTrue() {
  return true;
}

function serverFalse() {
  return false;
}

export function readRaw(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

export function useStoredRaw(key: string): string | null | undefined {
  return useSyncExternalStore(subscribe, () => readRaw(key), serverSnapshot);
}

export function useIsClient() {
  return useSyncExternalStore(noop, clientTrue, serverFalse);
}
