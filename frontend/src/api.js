import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

export const getLeads = (params = {}) => api.get('/leads', { params })
export const getLead = (id) => api.get(`/leads/${id}`)
export const updateLeadStatus = (id, status) => api.put(`/leads/${id}/status`, { status })
export const deleteLead = (id) => api.delete(`/leads/${id}`)
export const deleteLeads = (params = {}) => api.delete('/leads', { params })
export const deleteCompany = (id) => api.delete(`/companies/${id}`)
export const deleteCompanies = (params = {}) => api.delete('/companies', { params })


export const getStats = () => api.get('/stats')
export const getPipelineStatus = () => api.get('/pipeline-status')

export const getICP = () => api.get('/icp')
export const updateICP = (data) => api.post('/icp', data)

export const exportCSV = () => `${window.location.origin}/api/export/csv`
export const exportJSON = () => api.get('/export/json')

// Pipeline actions (fully routed through /api with extended 5m timeout to prevent browser-side failures)
export const discoverCompanies = () => api.post('/discover-companies-db', null, { timeout: 300000 })
export const discoverWebsites = () => api.post('/discover-websites', null, { timeout: 300000 })
export const scoreCompanies = () => api.post('/score-companies', null, { timeout: 300000 })
export const generateLeads = (limit = 30) => api.post(`/generate-leads-from-companies?limit=${limit}`, null, { timeout: 300000 })
export const verifyAll = () => api.post('/verify-all', null, { timeout: 300000 })
export const sendApproved = () => api.post('/campaign/send-approved', null, { timeout: 300000 })
export const getIntegrationsStatus = () => api.get('/integrations/status')
export const getCompanies = () => api.get('/companies-db')

// Cold email outreach actions
export const getColdEmail = (id) => api.get(`/leads/${id}/cold-email`)
export const sendColdEmail = (id) => api.post(`/leads/${id}/send-email`)

export default api
