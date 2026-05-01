import { useEffect, useId, useRef, useState, type ReactNode } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { cn } from '../../lib/cn';

interface TooltipProps {
  content: ReactNode;
  children?: ReactNode;
  label?: string;
}

export function Tooltip({ content, children, label }: TooltipProps) {
  const [open, setOpen] = useState(false);
  const id = useId();
  const wrapRef = useRef<HTMLSpanElement>(null);
  const isMobile = useIsMobile();

  useEffect(() => {
    if (!open) return;
    function onDocClick(e: MouseEvent) {
      if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') setOpen(false);
    }
    document.addEventListener('mousedown', onDocClick);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDocClick);
      document.removeEventListener('keydown', onKey);
    };
  }, [open]);

  const trigger = (
    <button
      type="button"
      aria-label={label ? `Help: ${label}` : 'Help'}
      aria-expanded={open}
      aria-describedby={open ? id : undefined}
      onClick={(e) => {
        e.stopPropagation();
        setOpen((v) => !v);
      }}
      className="inline-flex h-5 w-5 items-center justify-center rounded-full bg-line text-muted text-[11px] font-bold hover:bg-navy hover:text-white transition-colors no-tap-highlight"
    >
      i
    </button>
  );

  return (
    <span ref={wrapRef} className="relative inline-flex items-center gap-1.5">
      {children}
      {trigger}
      <AnimatePresence>
        {open && !isMobile && (
          <motion.div
            id={id}
            role="tooltip"
            initial={{ opacity: 0, y: 4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 4 }}
            transition={{ duration: 0.15 }}
            className="absolute left-0 top-full mt-2 z-30 w-64 rounded-lg bg-navy text-white text-sm leading-snug p-3 shadow-pop"
          >
            {content}
          </motion.div>
        )}
      </AnimatePresence>
      <AnimatePresence>
        {open && isMobile && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 bg-black/40 flex items-end"
            onClick={() => setOpen(false)}
          >
            <motion.div
              initial={{ y: 60 }}
              animate={{ y: 0 }}
              exit={{ y: 60 }}
              transition={{ type: 'spring', damping: 28, stiffness: 280 }}
              role="tooltip"
              id={id}
              onClick={(e) => e.stopPropagation()}
              className={cn(
                'w-full bg-white rounded-t-2xl p-5 pb-8 max-h-[70vh] overflow-auto',
              )}
            >
              {label && (
                <div className="font-heading text-lg text-navy mb-2 uppercase tracking-wide">
                  {label}
                </div>
              )}
              <div className="text-ink leading-relaxed">{content}</div>
              <button
                type="button"
                className="mt-5 w-full h-12 rounded-lg bg-navy text-white font-semibold"
                onClick={() => setOpen(false)}
              >
                Got it
              </button>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </span>
  );
}

function useIsMobile() {
  const [isMobile, set] = useState(() =>
    typeof window === 'undefined' ? false : window.matchMedia('(max-width: 640px)').matches,
  );
  useEffect(() => {
    const mq = window.matchMedia('(max-width: 640px)');
    const onChange = () => set(mq.matches);
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, []);
  return isMobile;
}
