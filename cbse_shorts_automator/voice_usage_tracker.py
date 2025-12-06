#!/usr/bin/env python3
"""
File: voice_usage_tracker.py
Persistent quota tracking for Google Cloud TTS across multiple accounts.
Handles usage monitoring, account rotation, and fallback decisions.
"""

import os
import json
import datetime
from pathlib import Path

# ============================================================================
# QUOTA LIMITS (Monthly per Google Cloud Project)
# ============================================================================
GOOGLE_QUOTA_LIMITS = {
    'standard': 4_000_000,      # 4M chars/month (free)
    'wavenet': 1_000_000,       # 1M chars/month (free)
    'neural2': 1_000_000,       # 1M chars/month (free)
    'studio': 1_000_000,        # 1M chars/month (free)
    'journey': 100_000          # 100K chars/month (free)
}

# Using Neural2 exclusively
DEFAULT_VOICE_TYPE = 'neural2'
MONTHLY_QUOTA = GOOGLE_QUOTA_LIMITS[DEFAULT_VOICE_TYPE]

class VoiceUsageTracker:
    """
    Tracks TTS usage across multiple Google Cloud accounts and Edge TTS.
    Persists data in data/ folder for cross-session tracking.
    """
    
    def __init__(self, data_dir='data'):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        self.usage_file = os.path.join(data_dir, 'voice_usage_history.json')
        self.quota_file = os.path.join(data_dir, 'voice_quota_state.json')
        
        self.usage_history = self._load_usage_history()
        self.quota_state = self._load_quota_state()
    
    def _load_usage_history(self):
        """Load cumulative usage log (append-only)."""
        if os.path.exists(self.usage_file):
            try:
                with open(self.usage_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_usage_history(self):
        """Save usage history to disk."""
        with open(self.usage_file, 'w') as f:
            json.dump(self.usage_history, f, indent=2)
    
    def _load_quota_state(self):
        """Load current quota state per account."""
        if os.path.exists(self.quota_file):
            try:
                with open(self.quota_file, 'r') as f:
                    state = json.load(f)
                    # Reset if month changed
                    if self._should_reset_quota(state.get('last_reset')):
                        return self._initialize_quota_state()
                    return state
            except:
                return self._initialize_quota_state()
        return self._initialize_quota_state()
    
    def _initialize_quota_state(self):
        """Initialize fresh quota state."""
        return {
            'last_reset': datetime.datetime.now().strftime('%Y-%m'),
            'accounts': {}
        }
    
    def _should_reset_quota(self, last_reset_month):
        """Check if we've entered a new month (quota resets monthly)."""
        if not last_reset_month:
            return True
        current_month = datetime.datetime.now().strftime('%Y-%m')
        return current_month != last_reset_month
    
    def _save_quota_state(self):
        """Save quota state to disk."""
        with open(self.quota_file, 'w') as f:
            json.dump(self.quota_state, f, indent=2)
    
    def register_account(self, account_name):
        """Register a new Google Cloud account for tracking."""
        if account_name not in self.quota_state['accounts']:
            self.quota_state['accounts'][account_name] = {
                'used_chars': 0,
                'quota_limit': MONTHLY_QUOTA,
                'available': MONTHLY_QUOTA
            }
            self._save_quota_state()
    
    def get_account_status(self, account_name):
        """
        Get current quota status for an account.
        
        Returns:
            dict: {'used': int, 'available': int, 'limit': int, 'percent_used': float}
        """
        if account_name not in self.quota_state['accounts']:
            self.register_account(account_name)
        
        acc = self.quota_state['accounts'][account_name]
        return {
            'used': acc['used_chars'],
            'available': acc['available'],
            'limit': acc['quota_limit'],
            'percent_used': (acc['used_chars'] / acc['quota_limit']) * 100
        }
    
    def find_available_account(self, required_chars, account_names):
        """
        Find first account with sufficient quota.
        
        Args:
            required_chars: Characters needed for current video
            account_names: List of account names to check
        
        Returns:
            str or None: Account name with sufficient quota, or None if all exhausted
        """
        for acc_name in account_names:
            status = self.get_account_status(acc_name)
            if status['available'] >= required_chars:
                return acc_name
        return None
    
    def log_usage(self, account_name, provider, chars_used, voice_used, video_id=None):
        """
        Log TTS usage for tracking.
        
        Args:
            account_name: Account identifier (e.g., 'google_account1', 'edge')
            provider: 'google' or 'edge'
            chars_used: Number of characters synthesized
            voice_used: Voice name used
            video_id: Optional video identifier
        """
        # Update quota state (only for Google)
        if provider == 'google':
            if account_name not in self.quota_state['accounts']:
                self.register_account(account_name)
            
            acc = self.quota_state['accounts'][account_name]
            acc['used_chars'] += chars_used
            acc['available'] = acc['quota_limit'] - acc['used_chars']
            self._save_quota_state()
        
        # Append to usage history
        log_entry = {
            'timestamp': datetime.datetime.now().isoformat(),
            'account': account_name,
            'provider': provider,
            'chars': chars_used,
            'voice': voice_used,
            'video_id': video_id,
            'cost_usd': self._estimate_cost(provider, chars_used) if provider == 'google' else 0
        }
        self.usage_history.append(log_entry)
        self._save_usage_history()
    
    def _estimate_cost(self, provider, chars_used):
        """
        Estimate cost for Google TTS (after free tier).
        
        Args:
            provider: 'google' or 'edge'
            chars_used: Characters synthesized
        
        Returns:
            float: Estimated cost in USD (0 if within free tier)
        """
        if provider != 'google':
            return 0.0
        
        # Neural2 pricing: $16 per 1M chars after free 1M/month
        cost_per_million = 16.0
        return (chars_used / 1_000_000) * cost_per_million
    
    def get_summary(self):
        """
        Get usage summary across all accounts.
        
        Returns:
            dict: Summary statistics
        """
        summary = {
            'total_google_chars': 0,
            'total_edge_chars': 0,
            'total_cost_usd': 0,
            'accounts': []
        }
        
        for acc_name, acc_data in self.quota_state['accounts'].items():
            summary['total_google_chars'] += acc_data['used_chars']
            summary['accounts'].append({
                'name': acc_name,
                'used': acc_data['used_chars'],
                'available': acc_data['available'],
                'percent_used': (acc_data['used_chars'] / acc_data['quota_limit']) * 100
            })
        
        # Calculate Edge usage from history
        for entry in self.usage_history:
            if entry['provider'] == 'edge':
                summary['total_edge_chars'] += entry['chars']
            if entry['provider'] == 'google':
                summary['total_cost_usd'] += entry.get('cost_usd', 0)
        
        return summary
    
    def print_summary(self):
        """Print usage summary to console."""
        summary = self.get_summary()
        
        print("\n" + "="*60)
        print("📊 VOICE USAGE SUMMARY")
        print("="*60)
        
        print(f"\n🔵 Google Cloud TTS:")
        print(f"   Total Characters: {summary['total_google_chars']:,}")
        print(f"   Estimated Cost: ${summary['total_cost_usd']:.2f}")
        
        for acc in summary['accounts']:
            print(f"\n   📁 {acc['name']}:")
            print(f"      Used: {acc['used']:,} / {MONTHLY_QUOTA:,} chars ({acc['percent_used']:.1f}%)")
            print(f"      Available: {acc['available']:,} chars")
        
        print(f"\n🟢 Edge TTS (Fallback):")
        print(f"   Total Characters: {summary['total_edge_chars']:,}")
        print(f"   Cost: $0.00 (Free)")
        
        print("\n" + "="*60)