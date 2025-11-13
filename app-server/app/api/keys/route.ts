import { NextRequest, NextResponse } from 'next/server';
import { connectDB } from '@/lib/db';
import { ApiKey } from '@/lib/models';
import bcrypt from 'bcryptjs';
import crypto from 'crypto';

/**
 * API Key management endpoints
 * Handles creating, listing, and revoking API keys for users
 */

export async function GET(request: NextRequest) {
  try {
    await connectDB();

    const { searchParams } = new URL(request.url);
    const userId = searchParams.get('userId');

    if (!userId) {
      return NextResponse.json(
        { error: 'userId is required' },
        { status: 400 }
      );
    }

    // Get all API keys for the user (return only metadata, not actual keys)
    const apiKeys = await ApiKey.find({ userId })
      .select('-keyHash -__v')
      .sort({ createdAt: -1 });

    return NextResponse.json({
      apiKeys: apiKeys.map(key => ({
        id: key._id,
        name: key.name,
        keyPrefix: key.keyPrefix,
        isActive: key.isActive,
        lastUsedAt: key.lastUsedAt,
        createdAt: key.createdAt,
        revokedAt: key.revokedAt,
      })),
    });
  } catch (error) {
    console.error('Error fetching API keys:', error);
    return NextResponse.json(
      { error: 'Failed to fetch API keys' },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest) {
  try {
    await connectDB();

    const body = await request.json();
    const { userId, name } = body;

    // Validate input
    if (!userId) {
      return NextResponse.json(
        { error: 'userId is required' },
        { status: 400 }
      );
    }

    // Generate API key
    const apiKey = 'sk_' + generateRandomKey();
    const keyPrefix = apiKey.substring(0, 12); // Store "sk_abc123..." for display

    // Hash the API key for storage
    const keyHash = await bcrypt.hash(apiKey, 10);

    // Create API key in database
    const newApiKey = await ApiKey.create({
      userId,
      name: name || 'Default API Key',
      keyHash,
      keyPrefix,
      isActive: true,
    });

    return NextResponse.json(
      {
        message: 'API key created successfully',
        apiKey, // Only return the full key once on creation!
        keyInfo: {
          id: newApiKey._id,
          name: newApiKey.name,
          keyPrefix: newApiKey.keyPrefix,
          isActive: newApiKey.isActive,
          createdAt: newApiKey.createdAt,
        },
        warning: 'Save this API key now. You will not be able to see it again.',
      },
      { status: 201 }
    );
  } catch (error) {
    console.error('Error creating API key:', error);
    return NextResponse.json(
      { error: 'Failed to create API key' },
      { status: 500 }
    );
  }
}

export async function DELETE(request: NextRequest) {
  try {
    await connectDB();

    const { searchParams } = new URL(request.url);
    const keyId = searchParams.get('id');

    if (!keyId) {
      return NextResponse.json(
        { error: 'API key ID is required' },
        { status: 400 }
      );
    }

    // Mark key as revoked
    const apiKey = await ApiKey.findByIdAndUpdate(
      keyId,
      {
        isActive: false,
        revokedAt: new Date(),
      },
      { new: true }
    ).select('-keyHash -__v');

    if (!apiKey) {
      return NextResponse.json(
        { error: 'API key not found' },
        { status: 404 }
      );
    }

    return NextResponse.json({
      message: 'API key revoked successfully',
      apiKey: {
        id: apiKey._id,
        keyPrefix: apiKey.keyPrefix,
        isActive: apiKey.isActive,
        revokedAt: apiKey.revokedAt,
      },
    });
  } catch (error) {
    console.error('Error revoking API key:', error);
    return NextResponse.json(
      { error: 'Failed to revoke API key' },
      { status: 500 }
    );
  }
}

// Helper function to generate random API key
function generateRandomKey(): string {
  // Use crypto for secure random generation
  return crypto.randomBytes(24).toString('base64')
    .replace(/\+/g, '')
    .replace(/\//g, '')
    .replace(/=/g, '')
    .substring(0, 48);
}
