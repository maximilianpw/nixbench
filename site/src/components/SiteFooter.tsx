type SiteFooterProps = {
  text: string;
  href: string;
  label: string;
};

export function SiteFooter({ text, href, label }: SiteFooterProps) {
  return (
    <footer className="site-footer">
      <p dangerouslySetInnerHTML={{ __html: text }} />
      <a href={href}>{label}</a>
    </footer>
  );
}
