/**
 * Dynamic Resume Editor
 * 
 * Sophisticated resume editor with granular AI optimization.
 * Features:
 * - Full CRUD on sections and bullets
 * - Real-time AI suggestions
 * - Inline optimization
 * - Drag-and-drop reordering
 * - Version control
 * 
 * @author CV Optimizer Team
 * @version 1.0.0
 */

'use client';

import { useState, useEffect, useCallback } from 'react';
import { useParams, useRouter } from 'next/navigation';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from '@dnd-kit/core';
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import {
  PlusIcon,
  TrashIcon,
  SparklesIcon,
  ArrowPathIcon,
  EyeIcon,
  EyeSlashIcon,
  CheckIcon,
  XMarkIcon,
  ClockIcon,
  DocumentDuplicateIcon,
  ArrowDownTrayIcon
} from '@heroicons/react/24/outline';

// Types
interface BulletPoint {
  id: string;
  content: string;
  order_index: number;
  is_visible: boolean;
  ai_generated: boolean;
  ai_confidence?: number;
  has_metrics: boolean;
  has_action_verb: boolean;
  optimization_suggestions?: any[];
}

interface ResumeSection {
  id: string;
  section_type: string;
  title: string;
  subtitle?: string;
  date_range?: string;
  location?: string;
  description?: string;
  order_index: number;
  is_visible: boolean;
  ai_generated: boolean;
  ai_confidence?: number;
  bullets: BulletPoint[];
}

interface StructuredResume {
  id: string;
  title: string;
  version: number;
  sections: ResumeSection[];
}

interface OptimizationSuggestion {
  type: string;
  title: string;
  description: string;
  suggested_content?: string;
  priority: number;
}

interface OptimizationResult {
  optimization_id: string;
  optimized_content: string;
  suggestions: OptimizationSuggestion[];
  quality_score: number;
}

export default function ResumeEditorPage() {
  const params = useParams();
  const router = useRouter();
  const resumeId = params.id as string;

  // State
  const [resume, setResume] = useState<StructuredResume | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [optimizing, setOptimizing] = useState<string | null>(null);
  const [selectedItem, setSelectedItem] = useState<{ type: string; id: string } | null>(null);
  const [optimizationResult, setOptimizationResult] = useState<OptimizationResult | null>(null);
  const [jobDescription, setJobDescription] = useState('');
  const [showJobDescModal, setShowJobDescModal] = useState(false);

  // Load resume
  useEffect(() => {
    loadResume();
  }, [resumeId]);

  const loadResume = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`http://localhost:8000/api/v1/resumes/${resumeId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setResume(data);
      } else {
        console.error('Failed to load resume');
      }
    } catch (error) {
      console.error('Error loading resume:', error);
    } finally {
      setLoading(false);
    }
  };

  // Section CRUD
  const addSection = async (sectionType: string) => {
    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch(`http://localhost:8000/api/v1/resumes/${resumeId}/sections`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          section_type: sectionType,
          title: getSectionTitle(sectionType),
          order_index: resume?.sections.length || 0,
          is_visible: true,
          bullets: []
        })
      });

      if (response.ok) {
        await loadResume();
      }
    } catch (error) {
      console.error('Error adding section:', error);
    } finally {
      setSaving(false);
    }
  };

  const updateSection = async (sectionId: string, updates: Partial<ResumeSection>) => {
    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      
      const response = await fetch(
        `http://localhost:8000/api/v1/resumes/${resumeId}/sections/${sectionId}`,
        {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(updates)
        }
      );

      if (response.ok) {
        await loadResume();
      }
    } catch (error) {
      console.error('Error updating section:', error);
    } finally {
      setSaving(false);
    }
  };

  const deleteSection = async (sectionId: string) => {
    if (!confirm('Delete this section?')) return;

    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      
      await fetch(
        `http://localhost:8000/api/v1/resumes/${resumeId}/sections/${sectionId}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      await loadResume();
    } catch (error) {
      console.error('Error deleting section:', error);
    } finally {
      setSaving(false);
    }
  };

  // Bullet CRUD
  const addBullet = async (sectionId: string) => {
    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      
      const section = resume?.sections.find(s => s.id === sectionId);
      
      const response = await fetch(
        `http://localhost:8000/api/v1/resumes/${resumeId}/sections/${sectionId}/bullets`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            content: 'New bullet point - click to edit',
            order_index: section?.bullets.length || 0,
            is_visible: true
          })
        }
      );

      if (response.ok) {
        await loadResume();
      }
    } catch (error) {
      console.error('Error adding bullet:', error);
    } finally {
      setSaving(false);
    }
  };

  const updateBullet = async (sectionId: string, bulletId: string, content: string) => {
    try {
      const token = localStorage.getItem('token');
      
      await fetch(
        `http://localhost:8000/api/v1/resumes/${resumeId}/sections/${sectionId}/bullets/${bulletId}`,
        {
          method: 'PATCH',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ content })
        }
      );

      await loadResume();
    } catch (error) {
      console.error('Error updating bullet:', error);
    }
  };

  const deleteBullet = async (sectionId: string, bulletId: string) => {
    try {
      setSaving(true);
      const token = localStorage.getItem('token');
      
      await fetch(
        `http://localhost:8000/api/v1/resumes/${resumeId}/sections/${sectionId}/bullets/${bulletId}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        }
      );

      await loadResume();
    } catch (error) {
      console.error('Error deleting bullet:', error);
    } finally {
      setSaving(false);
    }
  };

  // AI Optimization
  const optimizeItem = async (level: string, targetId?: string) => {
    setOptimizing(targetId || 'full');
    setShowJobDescModal(true);
  };

  const performOptimization = async () => {
    try {
      const token = localStorage.getItem('token');
      
      const response = await fetch(
        `http://localhost:8000/api/v1/resumes/${resumeId}/optimize`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            level: optimizing === 'full' ? 'full_resume' : 
                   selectedItem?.type === 'section' ? 'section' : 'bullet',
            target_id: selectedItem?.id,
            job_description: jobDescription || undefined
          })
        }
      );

      if (response.ok) {
        const result = await response.json();
        setOptimizationResult({
          optimization_id: result.id,
          optimized_content: result.optimized_content,
          suggestions: result.suggestions || [],
          quality_score: result.quality_score
        });
      }
    } catch (error) {
      console.error('Error optimizing:', error);
    } finally {
      setOptimizing(null);
      setShowJobDescModal(false);
    }
  };

  const applyOptimization = async () => {
    if (!optimizationResult) return;

    try {
      const token = localStorage.getItem('token');
      
      await fetch(
        `http://localhost:8000/api/v1/resumes/${resumeId}/optimizations/${optimizationResult.optimization_id}/apply`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            optimization_id: optimizationResult.optimization_id,
            apply_all_suggestions: true
          })
        }
      );

      await loadResume();
      setOptimizationResult(null);
    } catch (error) {
      console.error('Error applying optimization:', error);
    }
  };

  // Drag and drop sensors
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragEnd = async (event: DragEndEvent) => {
    const { active, over } = event;

    if (!over || active.id === over.id || !resume) return;

    const oldIndex = resume.sections.findIndex((s) => s.id === active.id);
    const newIndex = resume.sections.findIndex((s) => s.id === over.id);

    if (oldIndex === -1 || newIndex === -1) return;

    // Optimistically update UI
    const newSections = arrayMove(resume.sections, oldIndex, newIndex);
    setResume({ ...resume, sections: newSections });

    // Update order indices
    const updates = newSections.map((section, index) => ({
      id: section.id,
      order_index: index
    }));

    try {
      const token = localStorage.getItem('token');
      await fetch(
        `http://localhost:8000/api/v1/resumes/${resumeId}/sections/reorder`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({ items: updates })
        }
      );
    } catch (error) {
      console.error('Error reordering sections:', error);
      // Revert on error
      await loadResume();
    }
  };

  const getSectionTitle = (type: string): string => {
    const titles: Record<string, string> = {
      header: 'Header',
      summary: 'Professional Summary',
      experience: 'Work Experience',
      education: 'Education',
      skills: 'Skills',
      projects: 'Projects',
      certifications: 'Certifications',
      achievements: 'Achievements'
    };
    return titles[type] || 'Custom Section';
  };

  // Sortable Section Component
  function SortableSection({ section }: { section: ResumeSection }) {
    const {
      attributes,
      listeners,
      setNodeRef,
      transform,
      transition,
      isDragging,
    } = useSortable({ id: section.id });

    const style = {
      transform: CSS.Transform.toString(transform),
      transition,
      opacity: isDragging ? 0.5 : 1,
    };

    return (
      <div
        ref={setNodeRef}
        style={style}
        className={`bg-white rounded-lg shadow-sm border border-gray-200 ${
          isDragging ? 'shadow-lg' : ''
        }`}
      >
        {/* Section Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3 flex-1">
              <div
                {...attributes}
                {...listeners}
                className="cursor-move text-gray-400 hover:text-gray-600"
              >
                ⋮⋮
              </div>
              
              <input
                type="text"
                value={section.title}
                onChange={(e) =>
                  updateSection(section.id, { title: e.target.value })
                }
                className="text-lg font-semibold text-gray-900 border-none focus:ring-2 focus:ring-blue-500 rounded px-2 py-1"
              />
              
              {section.ai_generated && (
                <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                  <SparklesIcon className="h-3 w-3 mr-1" />
                  AI
                </span>
              )}
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => {
                  setSelectedItem({ type: 'section', id: section.id });
                  optimizeItem('section', section.id);
                }}
                className="p-2 text-purple-600 hover:bg-purple-50 rounded-md"
                title="Optimize section"
              >
                <SparklesIcon className="h-5 w-5" />
              </button>
              
              <button
                onClick={() =>
                  updateSection(section.id, {
                    is_visible: !section.is_visible
                  })
                }
                className="p-2 text-gray-600 hover:bg-gray-50 rounded-md"
                title={section.is_visible ? 'Hide' : 'Show'}
              >
                {section.is_visible ? (
                  <EyeIcon className="h-5 w-5" />
                ) : (
                  <EyeSlashIcon className="h-5 w-5" />
                )}
              </button>
              
              <button
                onClick={() => deleteSection(section.id)}
                className="p-2 text-red-600 hover:bg-red-50 rounded-md"
                title="Delete section"
              >
                <TrashIcon className="h-5 w-5" />
              </button>
            </div>
          </div>

          {/* Section Metadata */}
          <div className="mt-3 grid grid-cols-3 gap-4">
            <input
              type="text"
              placeholder="Subtitle (e.g., Company)"
              value={section.subtitle || ''}
              onChange={(e) =>
                updateSection(section.id, { subtitle: e.target.value })
              }
              className="text-sm text-gray-600 border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500"
            />
            
            <input
              type="text"
              placeholder="Date range"
              value={section.date_range || ''}
              onChange={(e) =>
                updateSection(section.id, { date_range: e.target.value })
              }
              className="text-sm text-gray-600 border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500"
            />
            
            <input
              type="text"
              placeholder="Location"
              value={section.location || ''}
              onChange={(e) =>
                updateSection(section.id, { location: e.target.value })
              }
              className="text-sm text-gray-600 border border-gray-300 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500"
            />
          </div>
        </div>

        {/* Bullets */}
        <div className="px-6 py-4 space-y-3">
          {section.bullets
            .sort((a, b) => a.order_index - b.order_index)
            .map((bullet) => (
              <div
                key={bullet.id}
                className="flex items-start space-x-3 group"
              >
                <span className="text-gray-400 mt-2">•</span>
                
                <div className="flex-1">
                  <textarea
                    value={bullet.content}
                    onChange={(e) =>
                      updateBullet(section.id, bullet.id, e.target.value)
                    }
                    onBlur={() => {/* Auto-save on blur */}}
                    className="w-full text-gray-700 border border-gray-200 rounded px-3 py-2 focus:ring-2 focus:ring-blue-500 resize-none"
                    rows={2}
                  />
                  
                  {/* Quality Indicators */}
                  <div className="mt-1 flex items-center space-x-2 text-xs">
                    {bullet.has_metrics && (
                      <span className="text-green-600">✓ Has metrics</span>
                    )}
                    {bullet.has_action_verb && (
                      <span className="text-green-600">✓ Action verb</span>
                    )}
                    {bullet.ai_confidence && (
                      <span className="text-gray-500">
                        Confidence: {bullet.ai_confidence}%
                      </span>
                    )}
                  </div>
                </div>

                <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button
                    onClick={() => {
                      setSelectedItem({ type: 'bullet', id: bullet.id });
                      optimizeItem('bullet', bullet.id);
                    }}
                    className="p-1 text-purple-600 hover:bg-purple-50 rounded"
                    title="Optimize bullet"
                  >
                    <SparklesIcon className="h-4 w-4" />
                  </button>
                  
                  <button
                    onClick={() => deleteBullet(section.id, bullet.id)}
                    className="p-1 text-red-600 hover:bg-red-50 rounded"
                    title="Delete bullet"
                  >
                    <TrashIcon className="h-4 w-4" />
                  </button>
                </div>
              </div>
            ))}

          <button
            onClick={() => addBullet(section.id)}
            className="flex items-center space-x-2 text-sm text-blue-600 hover:text-blue-700 mt-2"
          >
            <PlusIcon className="h-4 w-4" />
            <span>Add bullet point</span>
          </button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (!resume) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Resume not found</h2>
          <button
            onClick={() => router.push('/dashboard')}
            className="text-blue-600 hover:text-blue-700"
          >
            Return to dashboard
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/dashboard')}
                className="text-gray-600 hover:text-gray-900"
              >
                ← Back
              </button>
              <h1 className="text-xl font-semibold text-gray-900">
                {resume.title}
              </h1>
              <span className="text-sm text-gray-500">v{resume.version}</span>
              {saving && (
                <span className="text-sm text-blue-600 flex items-center">
                  <ArrowPathIcon className="h-4 w-4 animate-spin mr-1" />
                  Saving...
                </span>
              )}
            </div>

            <div className="flex items-center space-x-2">
              <button
                onClick={() => optimizeItem('full_resume')}
                className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-700 hover:to-blue-700"
              >
                <SparklesIcon className="h-5 w-5 mr-2" />
                Optimize All
              </button>
              
              <button
                onClick={() => {/* Export */}}
                className="inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50"
              >
                <ArrowDownTrayIcon className="h-5 w-5 mr-2" />
                Export
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <DndContext
          sensors={sensors}
          collisionDetection={closestCenter}
          onDragEnd={handleDragEnd}
        >
          <SortableContext
            items={resume.sections.map((s) => s.id)}
            strategy={verticalListSortingStrategy}
          >
            <div className="space-y-6">
              {resume.sections
                .sort((a, b) => a.order_index - b.order_index)
                .map((section) => (
                  <SortableSection key={section.id} section={section} />
                ))}
            </div>
          </SortableContext>
        </DndContext>

        {/* Add Section Button */}
        <div className="mt-6">
          <details className="bg-white rounded-lg shadow-sm border border-gray-200">
            <summary className="px-6 py-4 cursor-pointer text-blue-600 hover:text-blue-700 font-medium">
              + Add Section
            </summary>
            <div className="px-6 pb-4 grid grid-cols-2 gap-2">
              {['experience', 'education', 'skills', 'projects', 'certifications', 'achievements'].map(
                (type) => (
                  <button
                    key={type}
                    onClick={() => addSection(type)}
                    className="px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-50 rounded border border-gray-200"
                  >
                    {getSectionTitle(type)}
                  </button>
                )
              )}
            </div>
          </details>
        </div>
      </div>

      {/* Job Description Modal */}
      {showJobDescModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">
                AI Optimization
              </h3>
            </div>
            
            <div className="px-6 py-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Job Description (Optional)
              </label>
              <textarea
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                placeholder="Paste the job description to tailor the optimization..."
                className="w-full border border-gray-300 rounded-lg px-4 py-3 focus:ring-2 focus:ring-blue-500"
                rows={8}
              />
            </div>

            <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
              <button
                onClick={() => {
                  setShowJobDescModal(false);
                  setOptimizing(null);
                }}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
              <button
                onClick={performOptimization}
                className="px-4 py-2 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-md hover:from-purple-700 hover:to-blue-700"
              >
                Optimize
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Optimization Result Modal */}
      {optimizationResult && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  Optimization Result
                </h3>
                <p className="text-sm text-gray-500 mt-1">
                  Quality Score: {optimizationResult.quality_score}/100
                </p>
              </div>
              <button
                onClick={() => setOptimizationResult(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                <XMarkIcon className="h-6 w-6" />
              </button>
            </div>
            
            <div className="px-6 py-4">
              <div className="bg-gray-50 rounded-lg p-4 mb-4">
                <h4 className="text-sm font-medium text-gray-700 mb-2">
                  Optimized Content
                </h4>
                <div className="text-gray-900 whitespace-pre-wrap">
                  {optimizationResult.optimized_content}
                </div>
              </div>

              {optimizationResult.suggestions.length > 0 && (
                <div>
                  <h4 className="text-sm font-medium text-gray-700 mb-3">
                    Suggestions
                  </h4>
                  <div className="space-y-2">
                    {optimizationResult.suggestions.map((suggestion, idx) => (
                      <div
                        key={idx}
                        className="border border-gray-200 rounded-lg p-3"
                      >
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h5 className="font-medium text-gray-900">
                              {suggestion.title}
                            </h5>
                            <p className="text-sm text-gray-600 mt-1">
                              {suggestion.description}
                            </p>
                            {suggestion.suggested_content && (
                              <div className="mt-2 text-sm text-blue-600 bg-blue-50 rounded p-2">
                                {suggestion.suggested_content}
                              </div>
                            )}
                          </div>
                          <span className="ml-3 text-xs text-gray-500">
                            Priority: {suggestion.priority}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <div className="px-6 py-4 border-t border-gray-200 flex justify-end space-x-3">
              <button
                onClick={() => setOptimizationResult(null)}
                className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
              >
                Discard
              </button>
              <button
                onClick={applyOptimization}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 flex items-center"
              >
                <CheckIcon className="h-5 w-5 mr-2" />
                Apply Changes
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
