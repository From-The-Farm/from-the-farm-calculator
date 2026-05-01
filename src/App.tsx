import { CalculatorProvider, useCalculator } from './context/CalculatorContext';
import { Header } from './components/layout/Header';
import { Footer } from './components/layout/Footer';
import { ProgressBar } from './components/layout/ProgressBar';
import { IntroModal } from './components/layout/IntroModal';
import { WizardRouter } from './components/wizard/WizardRouter';

function Shell() {
  const { state } = useCalculator();
  return (
    <div className="flex min-h-full flex-col">
      <IntroModal />
      <Header />
      <ProgressBar step={state.step} />
      <main className="flex-1">
        <WizardRouter />
      </main>
      <Footer />
    </div>
  );
}

export default function App() {
  return (
    <CalculatorProvider>
      <Shell />
    </CalculatorProvider>
  );
}
