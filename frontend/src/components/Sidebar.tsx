import React, { useState } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '../contexts/AuthContext'
import clsx from 'clsx'
import {
  Shield, LayoutDashboard, Search, AlertTriangle,
  Activity, Bell, BookOpen, Droplets, BarChart2,
  Users, Settings, LogOut, ChevronLeft, ChevronRight,
  FileText, Lock
} from 'lucide-react'

interface NavItem {
  to: string
  icon: React.ReactNode
  label: string
  roles?: string[]
  badge?: string
}

const navItems: NavItem[] = [
  { to: '/dashboard', icon: <LayoutDashboard size={16}/>, label: 'Dashboard' },
  { to: '/analyzer', icon: <Search size={16}/>, label: 'Threat Analyzer' },
  { to: '/incidents', icon: <AlertTriangle size={16}/>, label: 'Incidents' },
  { to: '/alerts', icon: <Bell size={16}/>, label: 'Alerts' },
  { to: '/audit', icon: <BookOpen size={16}/>, label: 'Audit Ledger', roles: ['ADMIN', 'ANALYST'] },
  { to: '/watermark', icon: <Droplets size={16}/>, label: 'Watermarking' },
  { to: '/reports', icon: <FileText size={16}/>, label: 'Reports', roles: ['ADMIN', 'ANALYST'] },
  { to: '/users', icon: <Users size={16}/>, label: 'User Management', roles: ['ADMIN'] },
  { to: '/settings', icon: <Settings size={16}/>, label: 'Settings' },
]

export default function Sidebar() {
  const { user, logout, isAdmin, isAnalyst } = useAuth()
  const navigate = useNavigate()
  const [collapsed, setCollapsed] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  const filteredNav = navItems.filter(item => {
    if (!item.roles) return true
    if (item.roles.includes('ADMIN') && isAdmin) return true
    if (item.roles.includes('ANALYST') && isAnalyst) return true
    return false
  })

  return (
    <aside className={clsx(
      'h-screen flex flex-col border-r border-white/[0.06] bg-dark-800/80 backdrop-blur-md transition-all duration-300 sticky top-0',
      collapsed ? 'w-16' : 'w-60'
    )}>
      {/* Logo */}
      <div className={clsx('flex items-center gap-3 px-4 py-5 border-b border-white/[0.06]', collapsed && 'justify-center px-2')}>
        <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-gradient-to-br from-cyber-purple to-cyber-blue flex items-center justify-center">
          <Shield className="w-4 h-4 text-white" />
        </div>
        {!collapsed && (
          <div>
            <h1 className="text-sm font-bold text-gradient">DarkAI</h1>
            <p className="text-[10px] text-gray-600">Cyber Platform</p>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-4 px-2 space-y-0.5">
        {filteredNav.map(item => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => clsx(
              'nav-item',
              isActive && 'nav-item-active',
              collapsed && 'justify-center px-2'
            )}
            title={collapsed ? item.label : undefined}
          >
            {item.icon}
            {!collapsed && <span>{item.label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* User */}
      <div className="border-t border-white/[0.06] p-3">
        {!collapsed && (
          <div className="flex items-center gap-2.5 px-2 py-2 mb-2">
            <div className="w-7 h-7 rounded-full bg-gradient-to-br from-cyber-purple to-cyber-blue flex items-center justify-center text-xs font-bold text-white flex-shrink-0">
              {user?.username?.[0]?.toUpperCase()}
            </div>
            <div className="min-w-0">
              <p className="text-xs font-medium text-gray-200 truncate">{user?.username}</p>
              <p className="text-[10px] text-gray-500">{user?.role}</p>
            </div>
          </div>
        )}
        <button
          onClick={handleLogout}
          className={clsx('nav-item w-full text-red-400 hover:bg-red-500/10 hover:text-red-300', collapsed && 'justify-center px-2')}
        >
          <LogOut size={15} />
          {!collapsed && <span>Sign Out</span>}
        </button>
      </div>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(v => !v)}
        className="absolute -right-3 top-20 w-6 h-6 rounded-full bg-dark-700 border border-white/10 flex items-center justify-center text-gray-400 hover:text-gray-200 transition-colors"
      >
        {collapsed ? <ChevronRight size={12}/> : <ChevronLeft size={12}/>}
      </button>
    </aside>
  )
}
