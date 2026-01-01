'use client';

/**
 * VoiceCommandHelp Component
 *
 * Modal displaying voice command examples and usage instructions
 * Features:
 * - Command examples for all supported intents
 * - Bilingual support (English/Urdu)
 * - Categorized by command type
 * - Accessible modal with keyboard navigation
 */

import { useTranslations } from 'next-intl';
import { X, Mic, CheckCircle, Trash2, Edit, Filter, Volume2, HelpCircle } from 'lucide-react';
import { useLanguage } from '@/hooks/useLanguage';
import { getCommandExamples } from '@/lib/voice/commandParser';
import type { VoiceIntent } from '@/types/voice';
import { cn } from '@/lib/utils';

export interface VoiceCommandHelpProps {
  isOpen: boolean;
  onClose: () => void;
}

export function VoiceCommandHelp({ isOpen, onClose }: VoiceCommandHelpProps) {
  const t = useTranslations('voice');
  const { locale } = useLanguage();

  if (!isOpen) return null;

  // Command categories with icons and intents
  const commandCategories = [
    {
      title: locale === 'ur' ? 'کام بنائیں' : 'Create Tasks',
      icon: Mic,
      color: 'text-green-600 dark:text-green-400',
      bgColor: 'bg-green-500/10',
      borderColor: 'border-green-500/30',
      intents: ['CREATE_TASK' as VoiceIntent],
      available: true,
    },
    {
      title: locale === 'ur' ? 'کام مکمل کریں' : 'Complete Tasks',
      icon: CheckCircle,
      color: 'text-blue-600 dark:text-blue-400',
      bgColor: 'bg-blue-500/10',
      borderColor: 'border-blue-500/30',
      intents: ['COMPLETE_TASK' as VoiceIntent],
      available: true, // ✅ Phase 5 - Available now!
    },
    {
      title: locale === 'ur' ? 'کام حذف کریں' : 'Delete Tasks',
      icon: Trash2,
      color: 'text-red-600 dark:text-red-400',
      bgColor: 'bg-red-500/10',
      borderColor: 'border-red-500/30',
      intents: ['DELETE_TASK' as VoiceIntent],
      available: true, // ✅ Phase 5 - Available now!
    },
    {
      title: locale === 'ur' ? 'کام تبدیل کریں' : 'Update Tasks',
      icon: Edit,
      color: 'text-purple-600 dark:text-purple-400',
      bgColor: 'bg-purple-500/10',
      borderColor: 'border-purple-500/30',
      intents: ['UPDATE_TASK' as VoiceIntent],
      available: true, // ✅ Phase 5 - Available now!
    },
    {
      title: locale === 'ur' ? 'کام فلٹر کریں' : 'Filter Tasks',
      icon: Filter,
      color: 'text-orange-600 dark:text-orange-400',
      bgColor: 'bg-orange-500/10',
      borderColor: 'border-orange-500/30',
      intents: ['FILTER_TASKS' as VoiceIntent],
      available: true, // ✅ Phase 5 - Available now!
    },
    {
      title: locale === 'ur' ? 'کام سنیں' : 'Read Tasks Aloud',
      icon: Volume2,
      color: 'text-indigo-600 dark:text-indigo-400',
      bgColor: 'bg-indigo-500/10',
      borderColor: 'border-indigo-500/30',
      intents: ['READ_TASKS' as VoiceIntent],
      available: true, // ✅ Phase 6 - Available now!
    },
  ];

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
        role="dialog"
        aria-modal="true"
        aria-labelledby="voice-help-title"
      >
        <div
          className="glass-card max-w-2xl w-full max-h-[90vh] overflow-y-auto rounded-2xl border border-white/20 dark:border-gray-700/50 shadow-2xl"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="sticky top-0 glass-card px-6 py-4 border-b border-white/20 dark:border-gray-700/50 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <HelpCircle className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
              <h2
                id="voice-help-title"
                className="text-xl font-bold text-gray-900 dark:text-gray-100"
              >
                {t('help')}
              </h2>
            </div>
            <button
              onClick={onClose}
              className="p-2 rounded-lg hover:bg-white/10 transition-colors"
              aria-label="Close"
            >
              <X className="w-5 h-5 text-gray-600 dark:text-gray-400" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6 space-y-6">
            {/* Instructions */}
            <div className="glass-card p-4 rounded-lg border border-indigo-500/30">
              <p className="text-sm text-gray-700 dark:text-gray-300">
                {locale === 'ur' ? (
                  <>
                    <strong>کیسے استعمال کریں:</strong> مائیکروفون بٹن پر کلک کریں اور
                    نیچے دیے گئے مثالوں میں سے کوئی ایک کمانڈ بولیں۔ کمانڈ واضح اور آہستہ بولیں
                    بہترین نتائج کے لیے۔
                  </>
                ) : (
                  <>
                    <strong>How to use:</strong> Click the microphone button and speak any
                    of the commands shown below. Speak clearly and at a normal pace for best
                    results.
                  </>
                )}
              </p>
            </div>

            {/* Command Categories */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                {t('examples')}
              </h3>

              {commandCategories.map((category, categoryIndex) => {
                const Icon = category.icon;
                return (
                  <div
                    key={categoryIndex}
                    className={cn(
                      'glass-card p-4 rounded-lg border',
                      category.borderColor,
                      category.bgColor,
                      !category.available && 'opacity-60'
                    )}
                  >
                    <div className="flex items-center gap-2 mb-3">
                      <Icon className={cn('w-5 h-5', category.color)} />
                      <h4 className="font-semibold text-gray-900 dark:text-gray-100">
                        {category.title}
                      </h4>
                      {!category.available && (
                        <span className="text-xs px-2 py-1 rounded-full bg-gray-500/20 text-gray-600 dark:text-gray-400">
                          {locale === 'ur' ? 'جلد آ رہا ہے' : 'Coming Soon'}
                        </span>
                      )}
                    </div>

                    <div className="space-y-2">
                      {category.intents.map((intent) => {
                        const examples = getCommandExamples(intent, locale);
                        return examples.map((example, exampleIndex) => (
                          <div
                            key={`${intent}-${exampleIndex}`}
                            className="flex items-start gap-2 text-sm"
                          >
                            <span className="text-gray-400 mt-0.5">•</span>
                            <code className="text-gray-700 dark:text-gray-300 font-mono">
                              "{example}"
                            </code>
                          </div>
                        ));
                      })}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Tips */}
            <div className="glass-card p-4 rounded-lg border border-yellow-500/30 bg-yellow-500/10">
              <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-2">
                {locale === 'ur' ? '💡 تجاویز' : '💡 Tips'}
              </h4>
              <ul className="text-sm text-gray-700 dark:text-gray-300 space-y-1">
                <li className="flex items-start gap-2">
                  <span>•</span>
                  <span>
                    {locale === 'ur'
                      ? 'پس منظر کا شور کم کریں بہترین شناخت کے لیے'
                      : 'Minimize background noise for best recognition'}
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <span>•</span>
                  <span>
                    {locale === 'ur'
                      ? 'عام رفتار سے بولیں - بہت تیز یا بہت آہستہ نہیں'
                      : 'Speak at a normal pace - not too fast or slow'}
                  </span>
                </li>
                <li className="flex items-start gap-2">
                  <span>•</span>
                  <span>
                    {locale === 'ur'
                      ? 'Chrome یا Edge بہترین نتائج کے لیے استعمال کریں'
                      : 'Use Chrome or Edge browsers for best results'}
                  </span>
                </li>
              </ul>
            </div>
          </div>

          {/* Footer */}
          <div className="sticky bottom-0 glass-card px-6 py-4 border-t border-white/20 dark:border-gray-700/50 flex justify-end">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-medium transition-colors"
            >
              {locale === 'ur' ? 'بند کریں' : 'Close'}
            </button>
          </div>
        </div>
      </div>
    </>
  );
}
