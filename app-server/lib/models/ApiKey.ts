import mongoose, { Document, Schema, Types } from 'mongoose';

export interface IApiKey extends Document {
  userId: Types.ObjectId;
  name?: string;
  keyHash: string;
  keyPrefix: string; // Store first 8 chars for display (e.g., "sk_abc123")
  isActive: boolean;
  lastUsedAt?: Date;
  createdAt: Date;
  revokedAt?: Date;
}

const ApiKeySchema = new Schema<IApiKey>(
  {
    userId: {
      type: Schema.Types.ObjectId,
      ref: 'User',
      required: true,
      index: true,
    },
    name: {
      type: String,
      trim: true,
    },
    keyHash: {
      type: String,
      required: true,
      unique: true,
      index: true,
    },
    keyPrefix: {
      type: String,
      required: true,
    },
    isActive: {
      type: Boolean,
      default: true,
      index: true,
    },
    lastUsedAt: {
      type: Date,
    },
    createdAt: {
      type: Date,
      default: Date.now,
    },
    revokedAt: {
      type: Date,
    },
  },
  {
    timestamps: false, // Use manual timestamps
  }
);

// Indexes for performance
ApiKeySchema.index({ userId: 1, isActive: 1 });
ApiKeySchema.index({ keyHash: 1 });

export const ApiKey = mongoose.models.ApiKey || mongoose.model<IApiKey>('ApiKey', ApiKeySchema);
