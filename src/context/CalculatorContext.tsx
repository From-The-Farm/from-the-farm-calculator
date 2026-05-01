import { createContext, useContext, useMemo, useReducer, type ReactNode } from 'react';
import type {
  AnimalKey,
  CalculatorInput,
  Step1Data,
  Step2Data,
  Step3Data,
  Step4Data,
  WizardState,
} from '../lib/types';
import { ANIMAL_PROFILES, FALLBACK_DEFAULTS } from '../lib/animalDefaults';

const INITIAL_STATE: WizardState = {
  step: 1,
  step1: { ...FALLBACK_DEFAULTS.step1 },
  step2: structuredClone(FALLBACK_DEFAULTS.step2),
  step3: { method: 'cut', bundleWeight: 20 },
  step4: { mode: 'percent', profitDollar: 1500, profitPct: 25 },
  step5: { cutOverrides: {} },
};

type Action =
  | { type: 'SET_ANIMAL'; animal: AnimalKey }
  | { type: 'UPDATE_STEP1'; patch: Partial<Step1Data> }
  | { type: 'UPDATE_STEP2'; patch: Partial<Step2Data> }
  | { type: 'UPDATE_STEP3'; patch: Partial<Step3Data> }
  | { type: 'UPDATE_STEP4'; patch: Partial<Step4Data> }
  | { type: 'SET_CUT_OVERRIDE'; cutId: string; price: number | null }
  | { type: 'RESET_CUT_OVERRIDES' }
  | { type: 'NEXT' }
  | { type: 'BACK' }
  | { type: 'JUMP_TO'; step: WizardState['step'] }
  | { type: 'RESET' };

function reducer(state: WizardState, action: Action): WizardState {
  switch (action.type) {
    case 'SET_ANIMAL': {
      const profile = ANIMAL_PROFILES[action.animal];
      return {
        ...state,
        step1: { ...state.step1, animal: action.animal, ...profile.step1 },
        step2: structuredClone(profile.step2),
        step5: { cutOverrides: {} },
      };
    }
    case 'UPDATE_STEP1':
      return { ...state, step1: { ...state.step1, ...action.patch } };
    case 'UPDATE_STEP2':
      return {
        ...state,
        step2: {
          feedVet: { ...state.step2.feedVet, ...(action.patch.feedVet ?? {}) },
          processing: { ...state.step2.processing, ...(action.patch.processing ?? {}) },
          shipping: { ...state.step2.shipping, ...(action.patch.shipping ?? {}) },
          marketing: { ...state.step2.marketing, ...(action.patch.marketing ?? {}) },
          storage: { ...state.step2.storage, ...(action.patch.storage ?? {}) },
        },
      };
    case 'UPDATE_STEP3':
      return { ...state, step3: { ...state.step3, ...action.patch } };
    case 'UPDATE_STEP4':
      return { ...state, step4: { ...state.step4, ...action.patch } };
    case 'SET_CUT_OVERRIDE': {
      const next = { ...state.step5.cutOverrides };
      if (action.price === null) {
        delete next[action.cutId];
      } else {
        next[action.cutId] = action.price;
      }
      return { ...state, step5: { cutOverrides: next } };
    }
    case 'RESET_CUT_OVERRIDES':
      return { ...state, step5: { cutOverrides: {} } };
    case 'NEXT':
      return { ...state, step: Math.min(5, state.step + 1) as WizardState['step'] };
    case 'BACK':
      return { ...state, step: Math.max(1, state.step - 1) as WizardState['step'] };
    case 'JUMP_TO':
      return { ...state, step: action.step };
    case 'RESET':
      return INITIAL_STATE;
    default:
      return state;
  }
}

interface CalculatorCtx {
  state: WizardState;
  input: CalculatorInput;
  setAnimal: (animal: AnimalKey) => void;
  updateStep1: (patch: Partial<Step1Data>) => void;
  updateStep2: (patch: Partial<Step2Data>) => void;
  updateStep3: (patch: Partial<Step3Data>) => void;
  updateStep4: (patch: Partial<Step4Data>) => void;
  setCutOverride: (cutId: string, price: number | null) => void;
  resetCutOverrides: () => void;
  next: () => void;
  back: () => void;
  jumpTo: (step: WizardState['step']) => void;
  reset: () => void;
}

const Ctx = createContext<CalculatorCtx | null>(null);

export function CalculatorProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, INITIAL_STATE);

  const value = useMemo<CalculatorCtx>(
    () => ({
      state,
      input: { step1: state.step1, step2: state.step2, step3: state.step3, step4: state.step4 },
      setAnimal: (animal) => dispatch({ type: 'SET_ANIMAL', animal }),
      updateStep1: (patch) => dispatch({ type: 'UPDATE_STEP1', patch }),
      updateStep2: (patch) => dispatch({ type: 'UPDATE_STEP2', patch }),
      updateStep3: (patch) => dispatch({ type: 'UPDATE_STEP3', patch }),
      updateStep4: (patch) => dispatch({ type: 'UPDATE_STEP4', patch }),
      setCutOverride: (cutId, price) =>
        dispatch({ type: 'SET_CUT_OVERRIDE', cutId, price }),
      resetCutOverrides: () => dispatch({ type: 'RESET_CUT_OVERRIDES' }),
      next: () => dispatch({ type: 'NEXT' }),
      back: () => dispatch({ type: 'BACK' }),
      jumpTo: (step) => dispatch({ type: 'JUMP_TO', step }),
      reset: () => dispatch({ type: 'RESET' }),
    }),
    [state],
  );

  return <Ctx.Provider value={value}>{children}</Ctx.Provider>;
}

export function useCalculator(): CalculatorCtx {
  const ctx = useContext(Ctx);
  if (!ctx) throw new Error('useCalculator must be used inside CalculatorProvider');
  return ctx;
}
