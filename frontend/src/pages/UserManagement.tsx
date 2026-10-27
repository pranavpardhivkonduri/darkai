import React, { useEffect, useState } from 'react'
import { Users, Shield, Lock } from 'lucide-react'
import api from '../lib/api'
import { User } from '../types'
import { formatDate } from '../lib/utils'
import { useAuth } from '../contexts/AuthContext'
import toast from 'react-hot-toast'
import clsx from 'clsx'

export default function UserManagement() {
  const { isAdmin } = useAuth()
  const [users, setUsers] = useState<User[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!isAdmin) return
    api.get('/auth/users')
      .then(r => setUsers(r.data))
      .catch(() => toast.error('Failed to load users'))
      .finally(() => setLoading(false))
  }, [isAdmin])

  if (!isAdmin) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3">
        <Lock className="w-12 h-12 text-gray-700" />
        <p className="text-gray-500">Admin access required</p>
      </div>
    )
  }

  const toggleActive = async (user: User) => {
    try {
      await api.patch(`/auth/users/${user.id}`, { is_active: !user.is_active })
      setUsers(prev => prev.map(u => u.id === user.id ? { ...u, is_active: !u.is_active } : u))
      toast.success(`User ${user.is_active ? 'deactivated' : 'activated'}`)
    } catch { toast.error('Failed to update user') }
  }

  const roleColors = {
    ADMIN: 'text-red-400 bg-red-500/10 border-red-500/30',
    ANALYST: 'text-amber-400 bg-amber-500/10 border-amber-500/30',
    USER: 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30',
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-100">User Management</h1>
        <p className="text-sm text-gray-500">Manage DarkAI platform users and roles</p>
      </div>

      {loading ? (
        <div className="text-center py-16 text-gray-500">Loading users…</div>
      ) : (
        <div className="glass-card overflow-hidden">
          <table className="data-table">
            <thead>
              <tr>
                <th>User</th>
                <th>Email</th>
                <th>Role</th>
                <th>MFA</th>
                <th>Status</th>
                <th>Last Login</th>
                <th>Action</th>
              </tr>
            </thead>
            <tbody>
              {users.map(user => (
                <tr key={user.id}>
                  <td>
                    <div className="flex items-center gap-2">
                      <div className="w-7 h-7 rounded-full bg-gradient-to-br from-cyber-purple to-cyber-blue flex items-center justify-center text-xs font-bold text-white">
                        {user.username[0].toUpperCase()}
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-200">{user.username}</p>
                        <p className="text-xs text-gray-500">{user.full_name}</p>
                      </div>
                    </div>
                  </td>
                  <td className="text-xs text-gray-400">{user.email}</td>
                  <td>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-medium border ${roleColors[user.role]}`}>
                      {user.role}
                    </span>
                  </td>
                  <td>
                    <span className={clsx('text-xs', user.mfa_enabled ? 'text-emerald-400' : 'text-gray-600')}>
                      {user.mfa_enabled ? '✓ Enabled' : '✗ Disabled'}
                    </span>
                  </td>
                  <td>
                    <span className={clsx('text-xs font-medium', user.is_active ? 'text-emerald-400' : 'text-red-400')}>
                      {user.is_active ? 'Active' : 'Locked'}
                    </span>
                  </td>
                  <td className="text-xs text-gray-500">
                    {user.last_login ? formatDate(user.last_login) : 'Never'}
                  </td>
                  <td>
                    <button
                      onClick={() => toggleActive(user)}
                      className={clsx('text-xs px-2 py-1 rounded border transition-all', user.is_active
                        ? 'border-red-500/30 text-red-400 hover:bg-red-500/10'
                        : 'border-emerald-500/30 text-emerald-400 hover:bg-emerald-500/10'
                      )}
                    >
                      {user.is_active ? 'Lock' : 'Unlock'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
