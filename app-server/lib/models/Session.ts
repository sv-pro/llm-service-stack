import mongoose, { Document, Schema, Types } from 'mongoose';

export interface ISession extends Document {
  userId: Types.ObjectId;
  title?: string;
  llmModel: string;
  metadata?: Record<string, any>;
  createdAt: Date;
  updatedAt: Date;
}

const SessionSchema = new Schema<ISession>(
  {
    userId: {
      type: Schema.Types.ObjectId,
      ref: 'User',
      required: true,
      index: true,
    },
    title: {
      type: String,
      trim: true,
    },
    llmModel: {
      type: String,
      default: 'gpt-3.5-turbo',
    },
    metadata: {
      type: Schema.Types.Mixed,
    },
  },
  {
    timestamps: true,
  }
);

// Indexes for performance
SessionSchema.index({ userId: 1, createdAt: -1 });

export const Session = mongoose.models.Session || mongoose.model<ISession>('Session', SessionSchema);
