export function Footer() {
  return (
    <footer className="border-t border-line bg-white mt-12">
      <div className="container-wizard py-6 text-sm text-muted flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2">
        <span>© {new Date().getFullYear()} From The Farm. Built for farmers.</span>
        <a
          href="mailto:hello@fromthefarm.com"
          className="text-navy hover:underline font-semibold"
        >
          hello@fromthefarm.com
        </a>
      </div>
    </footer>
  );
}
