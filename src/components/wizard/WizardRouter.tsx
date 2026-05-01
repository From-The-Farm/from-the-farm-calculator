import { AnimatePresence, motion } from 'framer-motion';
import { useCalculator } from '../../context/CalculatorContext';
import { Step1Animal } from './Step1Animal';
import { Step2Costs } from './Step2Costs';
import { Step3Method } from './Step3Method';
import { Step4Profit } from './Step4Profit';
import { Step5Results } from './Step5Results';

const STEPS = {
  1: Step1Animal,
  2: Step2Costs,
  3: Step3Method,
  4: Step4Profit,
  5: Step5Results,
} as const;

export function WizardRouter() {
  const { state } = useCalculator();
  const Step = STEPS[state.step];

  return (
    <AnimatePresence mode="wait" initial={false}>
      <motion.div
        key={state.step}
        initial={{ opacity: 0, x: 24 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -24 }}
        transition={{ duration: 0.3, ease: 'easeOut' }}
      >
        <Step />
      </motion.div>
    </AnimatePresence>
  );
}
