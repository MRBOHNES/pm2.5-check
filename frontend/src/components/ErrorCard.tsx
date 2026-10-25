interface Props {
  title: string;
  message: string;
  onRetry?: () => void;
}

/** A section-level failure with an optional retry button. */
export function ErrorCard({ title, message, onRetry }: Props) {
  return (
    <section className="card notice" role="alert">
      <p className="h3">{title}</p>
      <p className="muted">{message}.</p>
      {onRetry && <button className="btn" onClick={onRetry}>Try again</button>}
    </section>
  );
}
