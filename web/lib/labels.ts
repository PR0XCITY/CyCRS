export const TOKEN_LABELS: Record<string, string> = {
  v_stolen_creds: "stolen passwords",
  v_brute_force: "password guessing",
  v_ransomware: "ransomware",
  v_backdoor_c2: "backdoors",
  v_exploit_vuln: "unpatched software",
  v_phishing: "phishing",
  v_pretexting: "pretexting scams",
  vec_email: "malicious email",
  vec_remote_access: "remote access break-ins",
  v_dos: "denial of service",
  v_privilege_abuse: "staff misuse of access",
  v_theft: "device theft",
  v_loss: "lost devices",
  v_skimmer: "card skimmers",
  action_malware: "malware",
  all: "all incidents",
};

export const CATEGORY_LABELS: Record<string, string> = {
  hacking: "Hacking",
  malware: "Malware",
  social: "Social engineering",
  error: "Staff error",
  misuse: "Insider misuse",
  physical: "Physical theft",
};

export const ASSET_LABELS: Record<string, string> = {
  asset_server: "servers, website or cloud",
  asset_user_device: "computers and phones",
  asset_network: "payment and network links",
  asset_media: "stored customer records",
};

export function tokenLabel(t: string) {
  return TOKEN_LABELS[t] ?? t.replace(/^(v|vec|action)_/, "").replace(/_/g, " ");
}

export function categoryLabel(c: string) {
  return CATEGORY_LABELS[c] ?? c;
}

export function featureLabel(f: string) {
  if (f.startsWith("sector_")) return `sector: ${f.slice(7).replace(/_+/g, " ")}`;
  if (f.startsWith("size_")) return `size: ${f.slice(5)}`;
  return ASSET_LABELS[f] ?? f;
}
