import type { ReactNode } from "react";

import { formatStatus } from "../utils/format";

export type IconName =
  | "arrow"
  | "check"
  | "dashboard"
  | "document"
  | "inbox"
  | "logout"
  | "open"
  | "processing"
  | "send"
  | "sparkles"
  | "ticket"
  | "trash"
  | "upload"
  | "user";

type IconProps = {
  name: IconName;
  size?: number;
};

const iconPaths: Record<IconName, ReactNode> = {
  arrow: <path d="m9 18 6-6-6-6m6 6H3" />,
  check: <path d="M20 6 9 17l-5-5" />,
  dashboard: (
    <>
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
      <rect x="14" y="14" width="7" height="7" rx="1.5" />
    </>
  ),
  document: (
    <>
      <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8Z" />
      <path d="M14 2v6h6M8 13h8M8 17h6" />
    </>
  ),
  inbox: (
    <>
      <path d="M4 4h16l2 11h-6l-2 3h-4l-2-3H2Z" />
      <path d="M2 15v4a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-4" />
    </>
  ),
  logout: (
    <>
      <path d="M10 17l5-5-5-5M15 12H3" />
      <path d="M14 3h5a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-5" />
    </>
  ),
  open: (
    <>
      <circle cx="12" cy="12" r="9" />
      <path d="M12 7v5l3 2" />
    </>
  ),
  processing: (
    <>
      <path d="M12 3v4M12 17v4M3 12h4M17 12h4" />
      <path d="m5.6 5.6 2.8 2.8m7.2 7.2 2.8 2.8m0-12.8-2.8 2.8m-7.2 7.2-2.8 2.8" />
    </>
  ),
  send: (
    <>
      <path d="m22 2-7 20-4-9-9-4Z" />
      <path d="M22 2 11 13" />
    </>
  ),
  sparkles: (
    <>
      <path d="m12 3 1.1 3.2a4 4 0 0 0 2.7 2.7L19 10l-3.2 1.1a4 4 0 0 0-2.7 2.7L12 17l-1.1-3.2a4 4 0 0 0-2.7-2.7L5 10l3.2-1.1a4 4 0 0 0 2.7-2.7Z" />
      <path d="m19 16 .5 1.5L21 18l-1.5.5L19 20l-.5-1.5L17 18l1.5-.5Z" />
    </>
  ),
  ticket: (
    <>
      <path d="M3 6a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v3a3 3 0 0 0 0 6v3a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-3a3 3 0 0 0 0-6Z" />
      <path d="M13 6v2M13 11v2M13 16v2" />
    </>
  ),
  trash: (
    <>
      <path d="M3 6h18M8 6V4h8v2M19 6l-1 15H6L5 6" />
      <path d="M10 11v5M14 11v5" />
    </>
  ),
  upload: (
    <>
      <path d="M12 16V3M7 8l5-5 5 5" />
      <path d="M5 13H3v8h18v-8h-2" />
    </>
  ),
  user: (
    <>
      <circle cx="12" cy="8" r="4" />
      <path d="M4 21a8 8 0 0 1 16 0" />
    </>
  ),
};

export function Icon({ name, size = 18 }: IconProps) {
  return (
    <svg
      aria-hidden="true"
      className="icon"
      fill="none"
      height={size}
      viewBox="0 0 24 24"
      width={size}
    >
      <g stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.8">
        {iconPaths[name]}
      </g>
    </svg>
  );
}

export function BrandMark() {
  return (
    <span className="brand-mark" aria-hidden="true">
      <svg fill="none" viewBox="0 0 32 32">
        <path d="M8.3 22.4A9.6 9.6 0 1 1 25.6 16v3.2a3.2 3.2 0 0 1-3.2 3.2h-2.1" />
        <path d="M6.4 14.9v5.4a2.1 2.1 0 0 0 2.1 2.1h1.1v-9.6H8.5a2.1 2.1 0 0 0-2.1 2.1ZM25.6 14.9v5.4a2.1 2.1 0 0 1-2.1 2.1h-1.1v-9.6h1.1a2.1 2.1 0 0 1 2.1 2.1Z" />
        <path d="M17 22.4h3.3" />
        <circle cx="15.6" cy="22.4" r="1.4" />
      </svg>
    </span>
  );
}

type PageHeaderProps = {
  eyebrow: string;
  title: string;
  description: string;
  children?: ReactNode;
};

export function PageHeader({ eyebrow, title, description, children }: PageHeaderProps) {
  return (
    <header className="page-header">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
        <p className="page-description">{description}</p>
      </div>
      {children && <div className="page-header-actions">{children}</div>}
    </header>
  );
}

type MetricCardProps = {
  label: string;
  value: number;
  helper: string;
  icon: IconName;
  tone?: "accent" | "success" | "warning" | "neutral";
};

export function MetricCard({
  label,
  value,
  helper,
  icon,
  tone = "neutral",
}: MetricCardProps) {
  return (
    <article className={`metric-card metric-${tone}`}>
      <div className="metric-card-top">
        <div className="metric-copy">
          <span>{label}</span>
          <strong>{value}</strong>
        </div>
        <span className="metric-icon">
          <Icon name={icon} size={18} />
        </span>
      </div>
      <p>{helper}</p>
    </article>
  );
}

type StatusBadgeProps = {
  value: string;
  label?: string;
  variant?: "status" | "priority" | "ai";
};

export function StatusBadge({ value, label, variant = "status" }: StatusBadgeProps) {
  return (
    <span className={`badge badge-${variant} badge-${value}`}>
      <span className="badge-dot" aria-hidden="true" />
      {label ?? formatStatus(value)}
    </span>
  );
}
