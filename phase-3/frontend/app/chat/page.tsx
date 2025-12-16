"use client";

/**
 * Chat Page - Glass Morphism Redesign
 *
 * AI Chat Assistant with ChatKit widget
 * Preserves all existing ChatKit functionality
 */

import { ChatKitWidget } from "@/components/chatkit";
import { HeaderGreeting } from "@/components/molecules/HeaderGreeting";
import { GlassCard } from "@/components/atoms/GlassCard";
import { useEffect, useState } from "react";
import { getCurrentUser } from "@/lib/auth";
import { User } from "@/types";

export default function ChatPage() {
  const [user, setUser] = useState<User | null>(null);

  useEffect(() => {
    async function loadUser() {
      try {
        const currentUser = await getCurrentUser();
        if (currentUser) {
          setUser({
            id: currentUser.id,
            name: currentUser.name,
            email: currentUser.email,
            createdAt: currentUser.createdAt?.toISOString(),
            updatedAt: currentUser.updatedAt?.toISOString(),
          });
        }
      } catch (error) {
        console.error("Failed to load user:", error);
      }
    }

    loadUser();
  }, []);

  return (
    <div className="min-h-screen p-4 md:p-8">
      {/* Header */}
      <div className="mb-8">
        <HeaderGreeting
          userName={user?.name}
          title="AI Chat Assistant"
          subtitle="Manage your tasks using natural language conversations"
        />
      </div>

      {/* Chat Container */}
      <div className="max-w-4xl mx-auto">
        <GlassCard variant="elevated" className="p-6 overflow-hidden">
          <div className="w-full h-[600px] flex flex-col">
            <ChatKitWidget className="flex-1 w-full" />
          </div>
        </GlassCard>

        {/* Instructions */}
        <GlassCard variant="flat" className="mt-6 p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-4">
            How to use:
          </h2>
          <ul className="list-disc list-inside text-gray-700 dark:text-gray-300 space-y-2">
            <li>Ask to add a new task: &ldquo;Add task: Buy groceries&rdquo;</li>
            <li>List your tasks: &ldquo;Show me all my tasks&rdquo;</li>
            <li>Mark tasks as complete: &ldquo;Complete task 1&rdquo;</li>
            <li>Delete tasks: &ldquo;Delete task 2&rdquo;</li>
            <li>Update tasks: &ldquo;Update task 3 to &lsquo;Finish homework&rsquo;&rdquo;</li>
          </ul>
        </GlassCard>
      </div>
    </div>
  );
}
