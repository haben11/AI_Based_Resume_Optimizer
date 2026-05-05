const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

// Types
export interface BulletPoint {
  id: string;
  content: string;
  order_index: number;
  is_visible: boolean;
  ai_generated: boolean;
  ai_confidence?: number;
  has_metrics: boolean;
  has_action_verb: boolean;
  optimization_suggestions?: any[];
  created_at: string;
  updated_at?: string;
}

export interface ResumeSection {
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
  created_at: string;
  updated_at?: string;
}

export interface StructuredResume {
  id: string;
  user_id: string;
  original_resume_id?: string;
  title: string;
  version: number;
  is_active: boolean;
  sections: ResumeSection[];
  created_at: string;
  updated_at?: string;
}

export interface OptimizationRequest {
  level: 'full_resume' | 'section' | 'bullet' | 'sentence' | 'selection';
  target_id?: string;
  job_description?: string;
  user_instructions?: string;
}

export interface OptimizationResult {
  id: string;
  resume_id: string;
  level: string;
  target_id?: string;
  original_content: string;
  optimized_content?: string;
  suggestions?: OptimizationSuggestion[];
  status: string;
  quality_score?: number;
  applied: boolean;
  created_at: string;
  completed_at?: string;
}

export interface OptimizationSuggestion {
  type: string;
  title: string;
  description: string;
  suggested_content?: string;
  priority: number;
  reasoning?: string;
}

export interface AISuggestion {
  id: string;
  target_type: string;
  target_id: string;
  suggestion_type: string;
  title: string;
  description: string;
  suggested_content?: string;
  priority: number;
  dismissed: boolean;
  applied: boolean;
  created_at: string;
}

export interface ResumeVersion {
  id: string;
  resume_id: string;
  version_number: number;
  snapshot: any;
  change_summary?: string;
  created_at: string;
}

// Helper function to get auth headers
function getAuthHeaders(): HeadersInit {
  const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
  return {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` })
  };
}

// API Client
export const structuredResumeAPI = {
  // ========================================================================
  // Resume CRUD
  // ========================================================================
  
  async createResume(data: {
    title?: string;
    original_resume_id?: string;
    sections?: any[];
  }): Promise<StructuredResume> {
    const response = await fetch(`${API_BASE}/resumes/`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      throw new Error('Failed to create resume');
    }
    
    return response.json();
  },
  
  async listResumes(activeOnly: boolean = true): Promise<StructuredResume[]> {
    const response = await fetch(
      `${API_BASE}/resumes/?active_only=${activeOnly}`,
      {
        headers: getAuthHeaders()
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to list resumes');
    }
    
    return response.json();
  },
  
  async getResume(resumeId: string): Promise<StructuredResume> {
    const response = await fetch(`${API_BASE}/resumes/${resumeId}`, {
      headers: getAuthHeaders()
    });
    
    if (!response.ok) {
      throw new Error('Failed to get resume');
    }
    
    return response.json();
  },
  
  async updateResume(
    resumeId: string,
    data: { title?: string; is_active?: boolean }
  ): Promise<StructuredResume> {
    const response = await fetch(`${API_BASE}/resumes/${resumeId}`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify(data)
    });
    
    if (!response.ok) {
      throw new Error('Failed to update resume');
    }
    
    return response.json();
  },
  
  async deleteResume(resumeId: string): Promise<void> {
    const response = await fetch(`${API_BASE}/resumes/${resumeId}`, {
      method: 'DELETE',
      headers: getAuthHeaders()
    });
    
    if (!response.ok) {
      throw new Error('Failed to delete resume');
    }
  },
  
  // ========================================================================
  // Section CRUD
  // ========================================================================
  
  async createSection(resumeId: string, data: {
    section_type: string;
    title: string;
    subtitle?: string;
    date_range?: string;
    location?: string;
    description?: string;
    order_index?: number;
    is_visible?: boolean;
    bullets?: any[];
  }): Promise<ResumeSection> {
    const response = await fetch(
      `${API_BASE}/resumes/${resumeId}/sections`,
      {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(data)
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to create section');
    }
    
    return response.json();
  },
  
  async getSection(resumeId: string, sectionId: string): Promise<ResumeSection> {
    const response = await fetch(
      `${API_BASE}/resumes/${resumeId}/sections/${sectionId}`,
      {
        headers: getAuthHeaders()
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to get section');
    }
    
    return response.json();
  },
  
  async updateSection(
    resumeId: string,
    sectionId: string,
    data: Partial<ResumeSection>
  ): Promise<ResumeSection> {
    const response = await fetch(
      `${API_BASE}/resumes/${resumeId}/sections/${sectionId}`,
      {
        method: 'PATCH',
        headers: getAuthHeaders(),
        body: JSON.stringify(data)
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to update section');
    }
    
    return response.json();
  },
  
  async deleteSection(resumeId: string, sectionId: string): Promise<void> {
    const response = await fetch(
      `${API_BASE}/resumes/${resumeId}/sections/${sectionId}`,
      {
        method: 'DELETE',
        headers: getAuthHeaders()
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to delete section');
    }
  },
  
  async reorderSections(
    resumeId: string,
    items: Array<{ id: string; order_index: number }>
  ): Promise<void> {
    const response = await fetch(
      `${API_BASE}/resumes/${resumeId}/sections/reorder`,
      {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ items })
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to reorder sections');
    }
  },
  
  // ========================================================================
  // Bullet CRUD
  // ========================================================================
  
  async createBullet(
    resumeId: string,
    sectionId: string,
    data: {
      content: string;
      order_index?: number;
      is_visible?: boolean;
    }
  ): Promise<BulletPoint> {
    const response = await fetch(
      `${API_BASE}/resumes/${resumeId}/sections/${sectionId}/bullets`,
      {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(data)
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to create bullet');
    }
    
    return response.json();
  },
  
  async updateBullet(
    resumeId: string,
    sectionId: string,
    bulletId: string,
    data: Partial<BulletPoint>
  ): Promise<BulletPoint> {
    const response = await fetch(
      `${API_BASE}/resumes/${resumeId}/sections/${sectionId}/bullets/${bulletId}`,
      {
        method: 'PATCH',
        headers: getAuthHeaders(),
        body: JSON.stringify(data)
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to update bullet');
    }
    
    return response.json();
  },
  
  async deleteBullet(
    resumeId: string,
    sectionId: string,
    bulletId: string
  ): Promise<void> {
    const response = await fetch(
      `${API_BASE}/resumes/${resumeId}/sections/${sectionId}/bullets/${bulletId}`,
      {
        method: 'DELETE',
        headers: getAuthHeaders()
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to delete bullet');
    }
  },
  
  async reorderBullets(
    resumeId: string,
    sectionId: string,
    items: Array<{ id: string; order_index: number }>
  ): Promise<void> {
    const response = await fetch(
      `${API_BASE}/resumes/${resumeId}/sections/${sectionId}/bullets/reorder`,
      {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ items })
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to reorder bullets');
    }
  },
  
  // ========================================================================
  // AI Optimization
  // ========================================================================
  
  async optimizeResume(
    resumeId: string,
    request: OptimizationRequest
  ): Promise<OptimizationResult> {
    const response = await fetch(
      `${API_BASE}/resumes/${resumeId}/optimize`,
      {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify(request)
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to optimize resume');
    }
    
    return response.json();
  },
  
  async getOptimization(
    resumeId: string,
    optimizationId: string
  ): Promise<OptimizationResult> {
    const response = await fetch(
      `${API_BASE}/resumes/${resumeId}/optimizations/${optimizationId}`,
      {
        headers: getAuthHeaders()
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to get optimization');
    }
    
    return response.json();
  },
  
  async applyOptimization(
    resumeId: string,
    optimizationId: string,
    applyAllSuggestions: boolean = true,
    selectedSuggestions?: number[]
  ): Promise<void> {
    const response = await fetch(
      `${API_BASE}/resumes/${resumeId}/optimizations/${optimizationId}/apply`,
      {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          optimization_id: optimizationId,
          apply_all_suggestions: applyAllSuggestions,
          selected_suggestions: selectedSuggestions
        })
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to apply optimization');
    }
  },
  
  // ========================================================================
  // AI Suggestions
  // ========================================================================
  
  async getSuggestions(
    resumeId: string,
    targetId?: string
  ): Promise<AISuggestion[]> {
    const url = targetId
      ? `${API_BASE}/resumes/${resumeId}/suggestions?target_id=${targetId}`
      : `${API_BASE}/resumes/${resumeId}/suggestions`;
    
    const response = await fetch(url, {
      headers: getAuthHeaders()
    });
    
    if (!response.ok) {
      throw new Error('Failed to get suggestions');
    }
    
    return response.json();
  },
  
  async dismissSuggestion(
    resumeId: string,
    suggestionId: string
  ): Promise<void> {
    const response = await fetch(
      `${API_BASE}/resumes/${resumeId}/suggestions/${suggestionId}/dismiss`,
      {
        method: 'POST',
        headers: getAuthHeaders()
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to dismiss suggestion');
    }
  },
  
  // ========================================================================
  // Version Control
  // ========================================================================
  
  async createVersion(
    resumeId: string,
    changeSummary?: string
  ): Promise<ResumeVersion> {
    const response = await fetch(
      `${API_BASE}/resumes/${resumeId}/versions`,
      {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ change_summary: changeSummary })
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to create version');
    }
    
    return response.json();
  },
  
  async listVersions(resumeId: string): Promise<ResumeVersion[]> {
    const response = await fetch(
      `${API_BASE}/resumes/${resumeId}/versions`,
      {
        headers: getAuthHeaders()
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to list versions');
    }
    
    return response.json();
  },
  
  async restoreVersion(
    resumeId: string,
    versionId: string
  ): Promise<void> {
    const response = await fetch(
      `${API_BASE}/resumes/${resumeId}/versions/restore`,
      {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({ version_id: versionId })
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to restore version');
    }
  },
  
  // ========================================================================
  // Export
  // ========================================================================
  
  async exportResume(
    resumeId: string,
    format: 'json' | 'markdown' | 'pdf' | 'docx',
    templateId?: string
  ): Promise<any> {
    const response = await fetch(
      `${API_BASE}/resumes/${resumeId}/export`,
      {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          format,
          template_id: templateId,
          include_hidden: false
        })
      }
    );
    
    if (!response.ok) {
      throw new Error('Failed to export resume');
    }
    
    if (format === 'pdf' || format === 'docx') {
      return response.blob();
    }
    
    return response.json();
  }
};
