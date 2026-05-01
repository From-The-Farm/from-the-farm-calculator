import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false };

  static getDerivedStateFromError(): State {
    return { hasError: true };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error('App error caught by ErrorBoundary:', error, info);
  }

  handleReload = (): void => {
    window.location.reload();
  };

  render(): ReactNode {
    if (!this.state.hasError) {
      return this.props.children;
    }
    return (
      <div className="min-h-full flex items-center justify-center bg-bg px-4 py-12">
        <div className="max-w-lg w-full rounded-lg border border-line bg-white shadow-card p-6 sm:p-10">
          <div className="text-xs font-bold uppercase tracking-[0.1em] text-gold mb-2">
            Something went sideways
          </div>
          <h1 className="font-heading uppercase tracking-tight text-2xl sm:text-3xl text-navy font-bold leading-tight">
            We hit a snag
          </h1>
          <p className="mt-3 text-base text-ink leading-relaxed">
            The pricing calculator ran into an unexpected error and couldn't
            finish that screen. Refresh the page and we'll start clean.
          </p>
          <div className="mt-6 flex flex-col sm:flex-row gap-3">
            <button
              type="button"
              onClick={this.handleReload}
              className="inline-flex items-center justify-center gap-2 h-12 px-5 rounded-lg bg-navy text-white font-heading uppercase tracking-wide text-[15px] font-semibold transition-colors hover:bg-navy/90 focus:outline-none focus-visible:ring-2 focus-visible:ring-gold ring-offset-2 ring-offset-bg"
            >
              Refresh the page
            </button>
            <a
              href="mailto:hello@fromthefarm.com"
              className="inline-flex items-center justify-center gap-2 h-12 px-5 rounded-lg bg-white text-navy border border-navy/20 font-heading uppercase tracking-wide text-[15px] font-semibold transition-colors hover:border-navy/50 hover:bg-navy/5 focus:outline-none focus-visible:ring-2 focus-visible:ring-gold ring-offset-2 ring-offset-bg"
            >
              Email us
            </a>
          </div>
        </div>
      </div>
    );
  }
}
