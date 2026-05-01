import { useEffect, useState } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { Button } from '../ui/Button';

const STORAGE_KEY = 'ftf-calc-intro-seen-v1';

export function IntroModal() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined') return;
    try {
      if (!window.localStorage.getItem(STORAGE_KEY)) setOpen(true);
    } catch {
      setOpen(true);
    }
  }, []);

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') dismiss();
    }
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open]);

  function dismiss() {
    try {
      window.localStorage.setItem(STORAGE_KEY, '1');
    } catch {
      // Storage unavailable — modal still dismisses for the session.
    }
    setOpen(false);
  }

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          className="fixed inset-0 z-50 bg-navy/60 backdrop-blur-sm flex items-center justify-center p-4"
          role="dialog"
          aria-modal="true"
          aria-labelledby="intro-title"
          onClick={dismiss}
        >
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.96 }}
            transition={{ type: 'spring', damping: 26, stiffness: 280 }}
            onClick={(e) => e.stopPropagation()}
            className="w-full max-w-md bg-white rounded-lg shadow-pop overflow-hidden"
          >
            <div className="bg-navy text-white px-6 py-5">
              <div className="text-xs font-semibold uppercase tracking-wider text-gold/90 mb-1">
                From The Farm
              </div>
              <h2 id="intro-title" className="font-heading text-2xl uppercase font-bold leading-tight">
                Find your fair price
              </h2>
            </div>

            <div className="px-6 py-5 space-y-3 text-ink leading-relaxed">
              <p>
                Five quick steps. We'll ask about your animal, costs, how you sell, and your profit
                goal — then back-solve a price per pound that actually pays you for your work.
              </p>
              <p className="text-sm text-muted">
                Defaults are pre-filled from real-world farm averages. Adjust anything that doesn't
                match your operation. Your numbers stay on this device.
              </p>
              <p className="text-xs text-muted italic">
                Estimates only. Final pricing should account for your own market, customer
                relationships, and brand.
              </p>
            </div>

            <div className="px-6 py-4 bg-bg/60 border-t border-line flex justify-end">
              <Button variant="primary" onClick={dismiss} autoFocus>
                Let's go →
              </Button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
